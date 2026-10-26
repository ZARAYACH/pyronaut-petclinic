"""Micronaut Data JDBC repositories.

Repositories are declared as Python ``Protocol`` classes. Pyronaut processes
the Micronaut Data annotations and creates the runtime implementation, so the
methods only need signatures.

Key concepts demonstrated here:

* Dialect-specific ``@JdbcRepository`` beans implement these shared contracts.
* ``CrudRepository[T, ID]`` provides standard CRUD methods.
* Method names such as ``findByOwnerId`` are parsed into queries.
* ``@Query`` is useful for native SQL when the method-name query would be too
  limited or when Oracle-specific SQL is clearer.
* ``@Join`` fetches relations eagerly so entity fields can stay non-null.
"""

from typing import Protocol

from java.time import Duration, LocalDate, Period

from micronaut.data.annotation import Join, Query
from micronaut.data.repository import GenericRepository

from .entities import Owner, Pet, PetType, Speciality, Vet, VetSpeciality, VetWithSpecialities, Visit


class OwnerRepository(GenericRepository[Owner, int], Protocol):
    """Owner queries used by search and list screens."""

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Owner | None: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findAllOrderByLastName(self) -> list[Owner]: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findByLastNameContainingIgnoreCaseOrderByLastName(self, lastName: str) -> list[Owner]: ...


class PetRepository(GenericRepository[Pet, int], Protocol):
    """Pet queries that eagerly fetch owner and type relationships."""

    @Join(value="type", type=Join.Type.FETCH)
    @Join(value="owner", type=Join.Type.FETCH)
    @Join(value="visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Pet | None: ...

    def findByOwnerId(self, ownerId: int) -> list[Pet]: ...


class PetTypeRepository(GenericRepository[PetType, int], Protocol):
    """Lookup repository for pet types shown in form select boxes."""

    def findOneById(self, id: int) -> PetType | None: ...

    @Query("SELECT * FROM TYPES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[PetType]: ...


class VisitRepository(GenericRepository[Visit, int], Protocol):
    """Visit queries with joined pet details for visit forms and owner pages."""

    def findOneById(self, id: int) -> Visit | None: ...

    def findByPetId(self, petId: int) -> list[Visit]: ...

    def findByPetName(self, petName: str) -> list[Visit]: ...
    def findByPetIdIn(self, petIds: list[int]) -> list[Visit]: ...
    def findByDescriptionContainingIgnoreCase(self, description: str) -> list[Visit]: ...
    def findByDateGreaterThanEqual(self, date: LocalDate) -> list[Visit]: ...
    def findByDateLessThanEqual(self, date: LocalDate) -> list[Visit]: ...
    def findByDurationGreaterThan(self, duration: Duration) -> list[Visit]: ...
    def findByDurationGreaterThanEqual(self, duration: Duration) -> list[Visit]: ...
    def findByDurationLessThanEqual(self, duration: Duration) -> list[Visit]: ...
    def findByPeriodGreaterThan(self, period: Period) -> list[Visit]: ...
    def findByPeriodGreaterThanEqual(self, period: Period) -> list[Visit]: ...
    def findByPeriodLessThanEqual(self, period: Period) -> list[Visit]: ...

    @Join(value="pet", type=Join.Type.FETCH)
    @Join(value="pet.type", type=Join.Type.FETCH)
    @Join(value="pet.owner", type=Join.Type.FETCH)
    def findByDateBetweenAndDurationLessThanEqualsAndPeriodLessThanEquals(
        self, fromDate: LocalDate, toDate: LocalDate, duration: Duration, period: Period
    ) -> list[Visit]: ...


class VetRepository(GenericRepository[Vet, int], Protocol):
    """Veterinarian list queries."""

    def findOneById(self, id: int) -> Vet | None: ...

    def findAllWithSpecialities(self) -> list[VetWithSpecialities]: ...


class SpecialityRepository(GenericRepository[Speciality, int], Protocol):
    """Lookup repository for specialities."""

    def findOneById(self, id: int) -> Speciality | None: ...

    @Query("SELECT * FROM SPECIALTIES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[Speciality]: ...


class VetSpecialityRepository(GenericRepository[VetSpeciality, VetSpeciality], Protocol):
    """Join-table repository used to persist vet speciality links."""

    def save(self, entity: VetSpeciality) -> None: ...

    @Query("SELECT s.* FROM SPECIALTIES s JOIN VET_SPECIALTIES vs ON s.ID = vs.SPECIALTY_ID WHERE vs.VET_ID = :vetId", nativeQuery=True)
    def findSpecialitiesByVetId(self, vetId: int) -> list[Speciality]: ...
