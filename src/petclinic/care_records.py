"""Oracle JSON duality documents for the existing owner, pet, and visit tables."""

from dataclasses import dataclass, field
from typing import Annotated, Protocol

from com.fasterxml.jackson.annotation import JsonFormat, JsonProperty
from jakarta.inject import Inject, Singleton
from jakarta.validation import Valid, Validator
from jakarta.validation.constraints import NotBlank, NotNull, Pattern
from java.time import LocalDate
from java.sql import SQLException
from micronaut.context.annotation import Requires
from micronaut.data.annotation import Id, JsonSubView, JsonView, MappedProperty, Relation
from micronaut.data.annotation.sql import JoinColumn
from micronaut.data.exceptions import DataAccessException, OptimisticLockException
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.repository import CrudRepository
from micronaut.http import HttpResponse, HttpStatus, MediaType
from micronaut.http.annotation import Body, Controller, Get, Put
from micronaut.serde.annotation import Serdeable

from .entities import Owner, Pet, Visit
from .validation import violation_path
from .errors import entity_not_found


@Serdeable
@dataclass
class DualityMetadata:
    etag: Annotated[str | None, NotBlank(message='The document must include its _metadata.etag value.')]
    asof: str | None = None


@JsonSubView(entity=Visit, operations=[JsonView.Operation.UPDATE])
@dataclass
class VisitCareSubView:
    id: Annotated[int, Id, MappedProperty('ID')]
    date: Annotated[LocalDate | None, MappedProperty('VISIT_DATE'), NotNull, JsonFormat(pattern="yyyy-MM-dd['T'HH:mm:ss]")]
    description: Annotated[str | None, MappedProperty('DESCRIPTION'), NotBlank]


@JsonSubView(entity=Pet, operations=[JsonView.Operation.UPDATE])
@dataclass
class PetCareSubView:
    id: Annotated[int, Id, MappedProperty('ID')]
    name: Annotated[str | None, MappedProperty('NAME'), NotBlank]
    birthDate: Annotated[LocalDate | None, MappedProperty('BIRTH_DATE'), NotNull, JsonFormat(pattern="yyyy-MM-dd['T'HH:mm:ss]")]
    visits: Annotated[list[Annotated[VisitCareSubView, Valid]] | None, MappedProperty('visits'), JoinColumn(name='ID', referencedColumnName='PET_ID'), Relation(Relation.Kind.ONE_TO_MANY)] = field(default_factory=list)

    def __post_init__(self):
        if self.visits is None:
            self.visits = []


@JsonView(value='OWNER_CARE_DV', entity=Owner, operations=[JsonView.Operation.UPDATE])
@dataclass
class OwnerCareView:
    id: Annotated[int, Id, MappedProperty('ID'), JsonProperty('_id')]
    firstName: Annotated[str | None, MappedProperty('FIRST_NAME'), NotBlank]
    lastName: Annotated[str | None, MappedProperty('LAST_NAME'), NotBlank]
    address: Annotated[str | None, MappedProperty('ADDRESS'), NotBlank]
    city: Annotated[str | None, MappedProperty('CITY'), NotBlank]
    telephone: Annotated[str | None, MappedProperty('TELEPHONE'), Pattern(regexp='[0-9]{1,10}', message='The telephone number must contain up to 10 digits.')]
    pets: Annotated[list[Annotated[PetCareSubView, Valid]] | None, MappedProperty('pets'), JoinColumn(name='ID', referencedColumnName='OWNER_ID'), Relation(Relation.Kind.ONE_TO_MANY)] = field(default_factory=list)
    metadata: Annotated[DualityMetadata | None, JsonProperty('_metadata'), NotNull(message='The document must include its _metadata.etag value.'), Valid] = None

    def __post_init__(self):
        if self.pets is None:
            self.pets = []


@Requires(env=['oracle'])
@JdbcRepository(dialect=Dialect.ORACLE)
class OwnerCareViewRepository(CrudRepository[OwnerCareView, int], Protocol):
    def findOneById(self, id: int) -> OwnerCareView | None: ...


@Requires(env=['oracle'])
@Singleton
class OwnerCareViewService:
    repository: Annotated[OwnerCareViewRepository, Inject]

    def find(self, owner_id: int) -> OwnerCareView | None:
        return self.repository.findOneById(owner_id)

    def update(self, document: OwnerCareView) -> OwnerCareView | None:
        self.repository.update(document)
        return self.find(document.id)


def missing_document():
    return entity_not_found()


def disallowed_operation(error) -> bool:
    cause = error
    while cause is not None and cause != None:
        if isinstance(cause, SQLException):
            sql = cause
            while sql is not None and sql != None:
                if sql.getErrorCode() in (40937, 40938, 40939, 40940, 42689):
                    return True
                sql = sql.getNextException()
        cause = cause.getCause()
    return False


@Controller('/')
@Requires(env=['oracle'])
class OwnerCareRecordController:
    service: Annotated[OwnerCareViewService, Inject]
    validator: Annotated[Validator, Inject]


    @Get('/owners/{ownerId}/care-record')
    def get_care_record(self, ownerId: int):
        document = self.service.find(ownerId)
        return document if document is not None else missing_document()


    @Put(value='/owners/{ownerId}/care-record', consumes=MediaType.APPLICATION_JSON)
    def update_care_record(self, ownerId: int, document: Annotated[OwnerCareView, Body]):
        violations = sorted(violation_path(v) + ': ' + str(v.getMessage()) for v in self.validator.validate(document))
        # The current Python integration does not cascade type-use @Valid on list
        # elements. Keep the same Jakarta constraints and validate each child bean
        # explicitly until that path is supported by the integration.
        for pet_index, pet in enumerate(document.pets):
            prefix = 'pets[' + str(pet_index) + ']'
            violations.extend(prefix + '.' + violation_path(v) + ': ' + str(v.getMessage()) for v in self.validator.validate(pet))
            for visit_index, visit in enumerate(pet.visits):
                visit_prefix = prefix + '.visits[' + str(visit_index) + ']'
                violations.extend(visit_prefix + '.' + violation_path(v) + ': ' + str(v.getMessage()) for v in self.validator.validate(visit))
        if violations:
            return HttpResponse.badRequest({'message': '; '.join(sorted(violations))})
        if ownerId != document.id:
            return HttpResponse.badRequest({'message': 'The document _id must match the owner in the URL.'})
        if self.service.find(ownerId) is None:
            return missing_document()
        try:
            updated = self.service.update(document)
        except OptimisticLockException:
            return HttpResponse.status(HttpStatus.CONFLICT).body({'message': 'This owner record changed after it was loaded. Reload it before saving.'})
        except DataAccessException as error:
            if disallowed_operation(error):
                return HttpResponse.badRequest({'message': 'The requested operation is not allowed.'})
            raise
        return updated if updated is not None else missing_document()
