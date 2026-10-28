"""Clinic spatial queries and atomic service catalog upserts in Micronaut Data."""

from dataclasses import dataclass, field
from typing import Annotated, Protocol
from jakarta.inject import Inject, Singleton
from jakarta.transaction import Transactional
from jakarta.validation.constraints import DecimalMin, Digits, Min, NotBlank, NotNull, Size
from java.math import BigDecimal
from micronaut.data.annotation import GeneratedValue, Id, Index, Join, MappedEntity, MappedProperty, Relation, Srid, Upsert
from micronaut.data.model.geo import Geometry, Point, Polygon
from micronaut.data.repository import GenericRepository
from micronaut.serde.annotation import Serdeable


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
