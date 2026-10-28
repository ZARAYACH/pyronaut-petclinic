"""Clinic spatial queries and atomic service catalog upserts in Micronaut Data."""

from dataclasses import dataclass, field
from typing import Annotated
from jakarta.validation.constraints import DecimalMin, Digits, Min, NotBlank, NotNull, Size
from java.math import BigDecimal
from micronaut.data.annotation import GeneratedValue, Id, Index, MappedEntity, MappedProperty, Relation, Srid
from micronaut.data.model.geo import Point, Polygon
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
