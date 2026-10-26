"""Micronaut Data entities used by the PetClinic sample.

The classes in this module are regular Python dataclasses with Micronaut
annotations attached through ``typing.Annotated``. Pyronaut reads these
annotations at build time and generates the Micronaut bean metadata needed for
Micronaut Data JDBC and Micronaut Serialization.

Key concepts demonstrated here:

* ``@MappedEntity`` maps a Python class to a database table.
* ``@Id`` and ``@GeneratedValue`` identify generated primary keys.
* ``@MappedProperty`` pins Python attribute names to explicit column names only
  when the convention-based name would be wrong or ambiguous.
* ``@Relation`` models foreign-key relationships between entities.
* ``@Serdeable`` lets entities be serialized for JSON responses.
"""

from dataclasses import dataclass, field
from typing import Annotated

from java.time import Duration, LocalDate, Period
from jakarta.validation.constraints import Digits, NotBlank, NotNull
from micronaut.core.annotation import Creator, Introspected
from micronaut.data.annotation import GeneratedValue, Id, MappedEntity, MappedProperty, Relation, Transient
from micronaut.serde.annotation import Serdeable
from micronaut.data.annotation.sql import ETaggable, GeneratedETag

from .etags import EMPTY_SPECIALITIES_HASH


@Serdeable
@MappedEntity("TYPES")
@dataclass
class PetType:
    """Lookup table entity for values such as cat, dog, and lizard."""

    name: Annotated[str, NotBlank, MappedProperty("NAME")]
    id: Annotated[int | None, Id, GeneratedValue] = None


@Serdeable
@MappedEntity("SPECIALTIES")
@dataclass
class Speciality:
    """Lookup table entity for veterinarian specialities."""

    name: Annotated[str, NotBlank, MappedProperty("NAME")]
    id: Annotated[int | None, Id, GeneratedValue] = None


@Serdeable
@MappedEntity("OWNERS")
@dataclass
class Owner:
    """A PetClinic owner.

    All business fields are required. Only the generated database ID defaults
    to ``None`` so new instances clearly represent unsaved rows.
    """

    firstName: Annotated[str, NotBlank, MappedProperty("FIRST_NAME")]
    lastName: Annotated[str, NotBlank, MappedProperty("LAST_NAME")]
    address: Annotated[str, NotBlank, MappedProperty("ADDRESS")]
    city: Annotated[str, NotBlank, MappedProperty("CITY")]
    telephone: Annotated[str | None, Digits(integer=10, fraction=0), MappedProperty("TELEPHONE")]
    id: Annotated[int | None, Id, GeneratedValue] = None
    pets: Annotated[list["Pet"], Relation(value=Relation.Kind.ONE_TO_MANY, mappedBy="owner")] = field(default_factory=list)

    def is_new(self) -> bool:
        return self.id is None


@Serdeable
@MappedEntity("PETS")
@dataclass
class Pet:
    """A pet belongs to one owner and has one pet type.

    ``Relation.Kind.MANY_TO_ONE`` tells Micronaut Data that ``type`` and
    ``owner`` are stored as foreign keys. Repository methods use ``@Join`` to
    fetch these non-null relationships when the UI needs them.
    """

    name: Annotated[str, NotBlank, MappedProperty("NAME")]
    birthDate: Annotated[LocalDate, NotNull, MappedProperty("BIRTH_DATE")]
    type: Annotated[PetType | None, NotNull, Relation(Relation.Kind.MANY_TO_ONE), MappedProperty("TYPE_ID")]
    owner: Annotated[Owner | None, Relation(Relation.Kind.MANY_TO_ONE), MappedProperty("OWNER_ID")]
    id: Annotated[int | None, Id, GeneratedValue] = None
    visits: Annotated[list["Visit"], Relation(value=Relation.Kind.ONE_TO_MANY, mappedBy="pet")] = field(default_factory=list)

    def is_new(self) -> bool:
        return self.id is None

    def get_type_id(self) -> int | None:
        return self.type.id if self.type is not None else None

    def get_owner_id(self) -> int | None:
        return self.owner.id if self.owner is not None else None


@Serdeable
@MappedEntity("VISITS")
@dataclass
class Visit:
    """A veterinary visit for a pet."""

    date: Annotated[LocalDate, NotNull, MappedProperty("VISIT_DATE")]
    description: Annotated[str, NotBlank, MappedProperty("DESCRIPTION")]
    pet: Annotated[Pet | None, Relation(Relation.Kind.MANY_TO_ONE), MappedProperty("PET_ID")]
    id: Annotated[int | None, Id, GeneratedValue] = None
    duration: Annotated[Duration, MappedProperty("DURATION")] = field(default_factory=lambda: Duration.ofMinutes(30))
    period: Annotated[Period, MappedProperty("FOLLOW_UP_PERIOD")] = field(default_factory=lambda: Period.ofMonths(6))

    def is_new(self) -> bool:
        return self.id is None


@Serdeable
@MappedEntity("VETS")
@ETaggable
@dataclass
class Vet:
    """ETag inputs follow the reference's positional SQL function signature."""

    id: Annotated[int | None, Id, GeneratedValue] = None
    firstName: Annotated[str | None, NotBlank, MappedProperty("FIRST_NAME")] = None
    lastName: Annotated[str | None, NotBlank, MappedProperty("LAST_NAME")] = None
    specialitiesHash: Annotated[str, MappedProperty("SPECIALITIES_ETAG_HASH")] = EMPTY_SPECIALITIES_HASH
    etag: Annotated[str | None, GeneratedETag(function="SYS_ROW_ETAG")] = None
    specialities: Annotated[list[Speciality], Transient] = field(default_factory=list)

    @staticmethod
    @Creator
    def from_columns(id: int | None, firstName: str, lastName: str,
                     specialitiesHash: str, etag: str | None) -> "Vet":
        return Vet(id=id, firstName=firstName, lastName=lastName,
                   specialitiesHash=specialitiesHash, etag=etag)


@Serdeable
@Introspected
@dataclass
class VetWithSpecialities:
    """Projection row returned by the vet list aggregate query."""

    id: int
    firstName: str
    lastName: str
    specialityRows: str | None


@MappedEntity("VET_SPECIALTIES")
@dataclass
class VetSpeciality:
    """The reference's pure join row, represented by its two foreign keys."""

    vetId: Annotated[int, MappedProperty("VET_ID")]
    specialityId: Annotated[int, MappedProperty("SPECIALTY_ID")]
