"""Clinic spatial queries and atomic service catalog upserts in Micronaut Data."""

from dataclasses import dataclass, field
from decimal import Decimal
from math import isfinite
from typing import Annotated, Protocol

from jakarta.inject import Inject, Singleton
from jakarta.transaction import Transactional
from jakarta.validation import Validator
from jakarta.validation.constraints import DecimalMin, Digits, Min, NotBlank, NotNull, Size
from java.math import BigDecimal
from micronaut.data.annotation import GeneratedValue, Id, Index, Join, MappedEntity, MappedProperty, Relation, Srid, Upsert
from micronaut.data.model.geo import Geometry, LineString, Point, Polygon
from micronaut.data.repository import GenericRepository
from micronaut.http import HttpResponse, MediaType
from micronaut.http.annotation import Body, Get, Post
from micronaut.serde.annotation import Serdeable
from micronaut.views import View

from .validation import violation_field


@MappedEntity("CLINICS")
@dataclass
class Clinic:
    name: Annotated[str, MappedProperty("NAME")]
    address: Annotated[str, MappedProperty("ADDRESS")]
    city: Annotated[str, MappedProperty("CITY")]
    acceptingNewPatients: Annotated[bool, MappedProperty("ACCEPTING_NEW_PATIENTS")]
    emergencyService: Annotated[bool, MappedProperty("EMERGENCY_SERVICE")]
    location: Annotated[Point, Srid(value=4326, type=Srid.CrsType.GEOGRAPHIC), MappedProperty("LOCATION")]
    serviceArea: Annotated[Polygon, Srid(value=4326, type=Srid.CrsType.GEOGRAPHIC), MappedProperty("SERVICE_AREA")]
    id: Annotated[int | None, Id, GeneratedValue] = None
    serviceOfferings: Annotated[list["ClinicServiceOffering"], Relation(value=Relation.Kind.ONE_TO_MANY, mappedBy="clinic")] = field(default_factory=list)


@Index(name="UK_CLINIC_SERVICE_CODE", columns=["CLINIC_ID", "SERVICE_CODE"], unique=True)
@MappedEntity("CLINIC_SERVICE_OFFERINGS")
@dataclass
class ClinicServiceOffering:
    clinic: Annotated[Clinic, Relation(Relation.Kind.MANY_TO_ONE), MappedProperty("CLINIC_ID")]
    serviceCode: Annotated[str, MappedProperty("SERVICE_CODE")]
    name: Annotated[str, MappedProperty("NAME")]
    description: Annotated[str | None, MappedProperty("DESCRIPTION")]
    price: Annotated[BigDecimal, MappedProperty("PRICE")]
    durationMinutes: Annotated[int, MappedProperty("DURATION_MINUTES")]
    id: Annotated[int | None, Id, GeneratedValue] = None


class ClinicRepository(GenericRepository[Clinic, int], Protocol):
    def findOneById(self, id: int) -> Clinic | None: ...
    def findAllOrderByName(self) -> list[Clinic]: ...
    def findByLocationNear(self, geometry: Geometry, distance: float) -> list[Clinic]: ...
    def findByLocationGeoWithin(self, geometry: Geometry) -> list[Clinic]: ...
    def findByServiceAreaGeoIntersects(self, geometry: Geometry) -> list[Clinic]: ...
    def findByAcceptingNewPatients(self, acceptingNewPatients: bool) -> list[Clinic]: ...
    def findByEmergencyService(self, emergencyService: bool) -> list[Clinic]: ...
    def findByAcceptingNewPatientsAndEmergencyService(self, acceptingNewPatients: bool, emergencyService: bool) -> list[Clinic]: ...


class ClinicServiceOfferingRepository(GenericRepository[ClinicServiceOffering, int], Protocol):
    @Upsert(conflictsOn=["clinic", "serviceCode"])
    def upsert(self, offering: ClinicServiceOffering) -> ClinicServiceOffering: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdOrderByServiceCode(self, clinicId: int) -> list[ClinicServiceOffering]: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdAndServiceCode(self, clinicId: int, serviceCode: str) -> ClinicServiceOffering | None: ...


@Serdeable
@dataclass
class Coordinate:
    latitude: float
    longitude: float


@Serdeable
@dataclass
class ClinicNearbyRequest:
    latitude: float
    longitude: float
    radiusMeters: float
    acceptingNewPatients: bool | None = None
    emergencyService: bool | None = None


@Serdeable
@dataclass
class ClinicCoordinatesRequest:
    coordinates: list[Coordinate]
    acceptingNewPatients: bool | None = None
    emergencyService: bool | None = None


@Serdeable
@dataclass
class ClinicServiceOfferingForm:
    serviceCode: Annotated[str | None, NotBlank(message="Service code is required"), Size(max=40, message="Service code must be at most 40 characters")] = None
    name: Annotated[str | None, NotBlank(message="Service name is required"), Size(max=100, message="Service name must be at most 100 characters")] = None
    description: Annotated[str | None, Size(max=500, message="Description must be at most 500 characters")] = None
    price: Annotated[BigDecimal | None, NotNull(message="Price is required"), DecimalMin(value="0.00", message="Price cannot be negative"), Digits(integer=8, fraction=2, message="Price must have at most two decimal places")] = None
    durationMinutes: Annotated[int | None, NotNull(message="Duration is required"), Min(value=1, message="Duration must be at least 1 minute")] = 30


@Serdeable
@dataclass
class ClinicServiceOfferingResponse:
    id: int
    clinicId: int
    serviceCode: str
    name: str
    description: str | None
    price: BigDecimal
    durationMinutes: int


@Singleton
class ClinicBranchService:
    clinics: Annotated[ClinicRepository, Inject]
    offerings: Annotated[ClinicServiceOfferingRepository, Inject]

    def filter_availability(self, clinics: list[Clinic], accepting: bool | None, emergency: bool | None) -> list[Clinic]:
        if accepting is None and emergency is None:
            return list(clinics)
        if accepting is not None and emergency is not None:
            matches = self.clinics.findByAcceptingNewPatientsAndEmergencyService(accepting, emergency)
        elif accepting is not None:
            matches = self.clinics.findByAcceptingNewPatients(accepting)
        else:
            matches = self.clinics.findByEmergencyService(emergency)
        ids = {clinic.id for clinic in matches}
        return [clinic for clinic in clinics if clinic.id in ids]

    @Transactional
    def upsert_offering(self, clinic: Clinic, form: ClinicServiceOfferingForm) -> ClinicServiceOffering:
        self.offerings.upsert(ClinicServiceOffering(
            clinic=clinic, serviceCode=form.serviceCode, name=form.name,
            description=form.description, price=form.price, durationMinutes=form.durationMinutes,
        ))
        # Resolve the natural key after the atomic upsert, including drivers that
        # return a generated candidate ID rather than the existing row's ID.
        return self.offerings.findByClinicIdAndServiceCode(clinic.id, form.serviceCode)


branch_service: Annotated[ClinicBranchService, Inject]
validator: Annotated[Validator, Inject]


def _clinic_model(clinic: Clinic) -> dict:
    return {"id": clinic.id, "name": clinic.name, "address": clinic.address, "city": clinic.city,
            "acceptingNewPatients": clinic.acceptingNewPatients, "emergencyService": clinic.emergencyService,
            "latitude": clinic.location.y(), "longitude": clinic.location.x()}


def _offering_model(offering: ClinicServiceOffering) -> dict:
    return {"id": offering.id, "serviceCode": offering.serviceCode, "name": offering.name,
            "description": offering.description or "", "price": format(Decimal(str(offering.price)), ".2f"), "durationMinutes": offering.durationMinutes}


def _coordinate(longitude: float, latitude: float) -> Point:
    if not isfinite(longitude) or not isfinite(latitude) or not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValueError("Coordinates must have longitude between -180 and 180 and latitude between -90 and 90.")
    return Point(longitude, latitude)


def _coordinates(request: ClinicCoordinatesRequest, minimum: int) -> list[Point]:
    if request.coordinates is None or len(request.coordinates) < minimum or any(c is None for c in request.coordinates):
        raise ValueError(f"This search requires at least {minimum} coordinates.")
    return [_coordinate(c.longitude, c.latitude) for c in request.coordinates]


def _cross(a, b, c):
    return (b.x() - a.x()) * (c.y() - a.y()) - (b.y() - a.y()) * (c.x() - a.x())


def _on_segment(a, b, p):
    return min(a.x(), b.x()) - 1e-10 <= p.x() <= max(a.x(), b.x()) + 1e-10 and min(a.y(), b.y()) - 1e-10 <= p.y() <= max(a.y(), b.y()) + 1e-10


def _intersects(a, b, c, d):
    x1, x2, x3, x4 = _cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b)
    if ((x1 > 1e-10 and x2 < -1e-10) or (x1 < -1e-10 and x2 > 1e-10)) and ((x3 > 1e-10 and x4 < -1e-10) or (x3 < -1e-10 and x4 > 1e-10)):
        return True
    return any(abs(cross) <= 1e-10 and _on_segment(start, end, point) for cross, start, end, point in (
        (x1, a, b, c), (x2, a, b, d), (x3, c, d, a), (x4, c, d, b)))


def _polygon(points: list[Point]) -> Polygon:
    shell = list(points)
    if shell[0].x() != shell[-1].x() or shell[0].y() != shell[-1].y():
        shell.append(shell[0])
    edges = len(shell) - 1
    if edges < 3 or any(shell[i].x() == shell[i + 1].x() and shell[i].y() == shell[i + 1].y() for i in range(edges)):
        raise ValueError("A polygon requires three distinct vertices and no zero-length edges.")
    for i in range(edges):
        for j in range(i + 1, edges):
            if j == i + 1 or (i == 0 and j == edges - 1):
                continue
            if _intersects(shell[i], shell[i + 1], shell[j], shell[j + 1]):
                raise ValueError("A polygon boundary cannot cross itself.")
    area = sum(shell[i].x() * shell[i + 1].y() - shell[i + 1].x() * shell[i].y() for i in range(edges))
    if abs(area) <= 1e-10:
        raise ValueError("A polygon must enclose a nonzero area.")
    if area < 0:
        shell.reverse()
    return Polygon([LineString(shell)])


@Get("/clinics")
@View("clinics/findClinics")
def find_clinics() -> dict:
    return {}


@Post(value="/clinics/nearby", consumes=MediaType.APPLICATION_JSON)
def nearby(request: Annotated[ClinicNearbyRequest, Body]):
    try:
        point = _coordinate(request.longitude, request.latitude)
        if not isfinite(request.radiusMeters) or request.radiusMeters <= 0:
            raise ValueError("Radius must be a positive finite number of meters.")
    except ValueError as error:
        return HttpResponse.badRequest({"message": str(error)})
    matches = branch_service.clinics.findByLocationNear(point, request.radiusMeters)
    return [_clinic_model(c) for c in branch_service.filter_availability(matches, request.acceptingNewPatients, request.emergencyService)]


@Post(value="/clinics/within", consumes=MediaType.APPLICATION_JSON)
def within(request: Annotated[ClinicCoordinatesRequest, Body]):
    try:
        polygon = _polygon(_coordinates(request, 3))
    except ValueError as error:
        return HttpResponse.badRequest({"message": str(error)})
    matches = branch_service.clinics.findByLocationGeoWithin(polygon)
    return [_clinic_model(c) for c in branch_service.filter_availability(matches, request.acceptingNewPatients, request.emergencyService)]


@Post(value="/clinics/intersects", consumes=MediaType.APPLICATION_JSON)
def intersects(request: Annotated[ClinicCoordinatesRequest, Body]):
    try:
        line = LineString(_coordinates(request, 2))
    except ValueError as error:
        return HttpResponse.badRequest({"message": str(error)})
    matches = branch_service.clinics.findByServiceAreaGeoIntersects(line)
    return [_clinic_model(c) for c in branch_service.filter_availability(matches, request.acceptingNewPatients, request.emergencyService)]


@Get("/clinics/{clinicId}/services")
@View("clinics/servicesList")
def clinic_services(clinicId: int):
    clinic = branch_service.clinics.findOneById(clinicId)
    if clinic is None:
        return HttpResponse.notFound({"error": "Clinic not found"})
    return {"clinic": _clinic_model(clinic), "services": [_offering_model(o) for o in branch_service.offerings.findByClinicIdOrderByServiceCode(clinicId)]}


@Get("/clinics/{clinicId}/services/new")
@View("clinics/createOrUpdateServiceForm")
def new_service(clinicId: int):
    clinic = branch_service.clinics.findOneById(clinicId)
    if clinic is None:
        return HttpResponse.notFound({"error": "Clinic not found"})
    return {"clinic": _clinic_model(clinic), "service": {"price": "0.00", "durationMinutes": 30}, "isNew": True, "validationErrors": {}}


@Get("/clinics/{clinicId}/services/{serviceCode}/edit")
@View("clinics/createOrUpdateServiceForm")
def edit_service(clinicId: int, serviceCode: str):
    offering = branch_service.offerings.findByClinicIdAndServiceCode(clinicId, serviceCode)
    if offering is None:
        return HttpResponse.notFound({"error": "Service offering not found"})
    return {"clinic": _clinic_model(offering.clinic), "service": _offering_model(offering), "isNew": False, "validationErrors": {}}


@Post(value="/clinics/{clinicId}/services", consumes=MediaType.APPLICATION_JSON)
def save_service(clinicId: int, form: Annotated[ClinicServiceOfferingForm, Body]):
    clinic = branch_service.clinics.findOneById(clinicId)
    if clinic is None:
        return HttpResponse.notFound({"message": "Clinic not found"})
    errors = {violation_field(v): str(v.getMessage()) for v in validator.validate(form)}
    if errors:
        return HttpResponse.badRequest({"message": "Validation failed", "errors": errors})
    offering = branch_service.upsert_offering(clinic, form)
    return ClinicServiceOfferingResponse(id=offering.id, clinicId=clinicId, serviceCode=offering.serviceCode,
        name=offering.name, description=offering.description, price=offering.price, durationMinutes=offering.durationMinutes)
