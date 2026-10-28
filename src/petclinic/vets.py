"""Veterinarian CRUD, speciality management and generated database ETags."""

from dataclasses import dataclass, field
from typing import Annotated

from jakarta.inject import Inject, Singleton
from jakarta.transaction import Transactional
from jakarta.validation import Validator
from jakarta.validation.constraints import NotBlank, Size
from micronaut.data.exceptions import OptimisticLockException
from micronaut.http import HttpResponse, HttpStatus, MediaType
from micronaut.http.annotation import Body, Controller, Delete, Get, Header, Post, Put, QueryValue
from micronaut.http.exceptions import HttpStatusException
from micronaut.http.server.exceptions import NotFoundException
from micronaut.scheduling.annotation import ExecuteOn
from micronaut.serde.annotation import Serdeable
from micronaut.views import View

from .entities import Speciality, Vet
from .etags import speciality_hash
from .repositories.vets import SpecialityRepository
from .repositories.vets import VetRepository
from .repositories.vets import VetSpecialityRepository
from petclinic.services.view_models import vet_view_models


def domain_error(status: HttpStatus, message: str):
    raise HttpStatusException(status, message)


@Serdeable
@dataclass
class VetForm:
    firstName: Annotated[str | None, NotBlank, Size(max=255)] = None
    lastName: Annotated[str | None, NotBlank, Size(max=255)] = None
    # The SDK coerces null elements of typed integer collections to zero.
    # Keep the input nullable here and enforce integer IDs in resolve().
    specialityIds: list[object] | None = field(default_factory=list)


@Serdeable
@dataclass
class SpecialityForm:
    id: int | None = None
    name: Annotated[str | None, NotBlank, Size(max=255)] = None


def speciality_model(speciality) -> dict:
    return {'id': speciality.id, 'name': speciality.name}


def vet_model(vet) -> dict:
    return {'id': vet.id, 'firstName': vet.firstName, 'lastName': vet.lastName,
            'specialities': [speciality_model(s) for s in vet.specialities], 'etag': vet.etag}


def expected_etag(value: str | None) -> str:
    if value is None or not value.strip():
        domain_error(HttpStatus.PRECONDITION_REQUIRED, 'ETag is missing.')
    return value[1:-1] if len(value) >= 2 and value.startswith('"') and value.endswith('"') else value


@Singleton
class VetService:
    vets: Annotated[VetRepository, Inject]
    specialities: Annotated[SpecialityRepository, Inject]
    links: Annotated[VetSpecialityRepository, Inject]

    def enriched(self, row) -> Vet:
        return Vet(id=row.id, firstName=row.firstName, lastName=row.lastName,
                   specialitiesHash=row.specialitiesHash, etag=row.etag,
                   specialities=list(self.links.findSpecialitiesByVetId(row.id)))

    def find_all(self) -> list[Vet]:
        return [self.enriched(v) for v in self.vets.findAllOrderByLastName()]

    def find(self, id: int) -> Vet:
        row = self.vets.findOneById(id)
        if row is None:
            domain_error(HttpStatus.NOT_FOUND, 'Entity not found.')
        return self.enriched(row)

    def find_speciality(self, id: int) -> Speciality:
        speciality = self.specialities.findOneById(id)
        if speciality is None:
            domain_error(HttpStatus.NOT_FOUND, 'Entity not found.')
        return speciality

    def resolve(self, ids) -> list[Speciality]:
        values = list(ids or [])
        # A Java null in an Object collection is GraalPy ForeignNone, whose
        # identity is different from Python None. Compare null values directly.
        if any(id is None or id == None for id in values):
            domain_error(HttpStatus.BAD_REQUEST, 'Each speciality must have an id.')
        if any(not isinstance(id, int) or isinstance(id, bool) or
               not -2147483648 <= id <= 2147483647 for id in values):
            domain_error(HttpStatus.BAD_REQUEST, 'Invalid request value.')
        requested = set(values)
        resolved = list(self.specialities.findAllByIdIn(sorted(requested))) if requested else []
        if len(resolved) != len(requested):
            domain_error(HttpStatus.BAD_REQUEST, 'One or more specialities were not found.')
        return resolved

    @Transactional
    def create(self, form: VetForm) -> Vet:
        selected = self.resolve(form.specialityIds)
        row = self.vets.save(Vet(firstName=form.firstName, lastName=form.lastName,
                                 specialitiesHash=speciality_hash(s.id for s in selected)))
        for speciality in selected:
            self.vets.insertSpecialityLink(row.id, speciality.id)
        return self.find(row.id)

    @Transactional
    def update(self, id: int, form: VetForm, etag: str | None) -> Vet:
        current = self.find(id)
        version = expected_etag(etag)
        selected = self.resolve(form.specialityIds)
        updated = Vet(id=current.id, firstName=form.firstName, lastName=form.lastName,
                      specialitiesHash=speciality_hash(s.id for s in selected), etag=version)
        try:
            self.vets.deleteSpecialityLinks(id)
            self.vets.update(updated)
            for speciality in selected:
                self.vets.insertSpecialityLink(id, speciality.id)
        except OptimisticLockException:
            domain_error(HttpStatus.PRECONDITION_FAILED, 'The entity etag has changed since it was loaded.')
        return self.find(id)

    @Transactional
    def delete(self, id: int, etag: str | None) -> None:
        version = expected_etag(etag)
        current = self.find(id)
        try:
            self.vets.deleteSpecialityLinks(id)
            self.vets.delete(Vet(id=id, firstName=current.firstName, lastName=current.lastName,
                                 specialitiesHash=current.specialitiesHash, etag=version))
        except OptimisticLockException:
            domain_error(HttpStatus.PRECONDITION_FAILED, 'The entity etag has changed since it was loaded.')

    def unique_speciality(self, name: str, current_id: int | None):
        existing = self.specialities.findByName(name)
        if existing is not None and existing.id != current_id:
            domain_error(HttpStatus.BAD_REQUEST, 'Speciality name already exists.')

    def create_speciality(self, form: SpecialityForm) -> Speciality:
        self.unique_speciality(form.name, None)
        return self.specialities.save(Speciality(name=form.name))

    def update_speciality(self, id: int, form: SpecialityForm) -> Speciality:
        self.find_speciality(id)
        self.unique_speciality(form.name, id)
        return self.specialities.update(Speciality(id=id, name=form.name))


@Controller('/vets')
@ExecuteOn('blocking')
class VetController:
    service: Annotated[VetService, Inject]
    validator: Annotated[Validator, Inject]

    def validate(self, form):
        if list(self.validator.validate(form)):
            domain_error(HttpStatus.BAD_REQUEST, 'Invalid request.')

    def response(self, vet, status=HttpStatus.OK):
        return (HttpResponse.status(status).header('ETag', '"' + vet.etag + '"')
                .header('Cache-Control', 'no-store').body(vet_model(vet)))

    @Get
    @View('vets/vetList')
    def page(self, saved: Annotated[bool, QueryValue(defaultValue='false')] = False):
        return {'vets': vet_view_models(self.service.find_all()), 'saved': saved}

    @Get('/html')
    @View('vets/vetList')
    def html(self, saved: Annotated[bool, QueryValue(defaultValue='false')] = False):
        return self.page(saved)

    @Get('/json')
    def listing(self):
        return [vet_model(v) for v in self.service.find_all()]

    @Get('/new')
    @View('vets/createOrUpdateVetForm')
    def new_vet(self):
        return {'vetForm': {'specialityIds': []}, 'specialities': list(self.service.specialities.findAllOrderByName()),
                'isNew': True, 'saved': False}

    @Get('/{id}/edit')
    @View('vets/createOrUpdateVetForm')
    def edit(self, id: int, saved: Annotated[bool, QueryValue(defaultValue='false')] = False):
        try:
            vet = self.service.find(id)
        except HttpStatusException:
            raise NotFoundException()
        return {'vetForm': {**vet_model(vet), 'specialityIds': [s.id for s in vet.specialities]},
                'specialities': list(self.service.specialities.findAllOrderByName()), 'isNew': False, 'saved': saved}

    @Post(consumes=MediaType.APPLICATION_JSON)
    def create(self, form: Annotated[VetForm, Body]):
        self.validate(form)
        return self.response(self.service.create(form), HttpStatus.CREATED)

    @Get('/{id}')
    def read(self, id: int):
        return self.response(self.service.find(id))

    @Put(value='/{id}', consumes=MediaType.APPLICATION_JSON)
    def update(self, id: int, form: Annotated[VetForm, Body],
               ifMatch: Annotated[str | None, Header('If-Match')] = None):
        self.validate(form)
        return self.response(self.service.update(id, form, ifMatch))

    @Delete('/{id}')
    def delete(self, id: int, ifMatch: Annotated[str | None, Header('If-Match')] = None):
        self.service.delete(id, ifMatch)
        return HttpResponse.noContent()

    @Get('/specialities')
    @View('vets/specialityList')
    def specialities(self, created: Annotated[bool, QueryValue(defaultValue='false')] = False,
                     changed: Annotated[bool, QueryValue(defaultValue='false')] = False):
        return {'specialities': list(self.service.specialities.findAllOrderByName()),
                'created': created, 'changed': changed}

    @Get('/specialities/json')
    def speciality_listing(self):
        return [speciality_model(s) for s in self.service.specialities.findAllOrderByName()]

    @Get('/specialities/new')
    @View('vets/createOrUpdateSpecialityForm')
    def new_speciality(self, duplicate: Annotated[bool, QueryValue(defaultValue='false')] = False):
        return {'specialityForm': {}, 'isNew': True, 'saved': False, 'duplicate': duplicate}

    @Get('/specialities/{id}/edit')
    @View('vets/createOrUpdateSpecialityForm')
    def edit_speciality(self, id: int, saved: Annotated[bool, QueryValue(defaultValue='false')] = False,
                       duplicate: Annotated[bool, QueryValue(defaultValue='false')] = False):
        try:
            speciality = self.service.find_speciality(id)
        except HttpStatusException:
            raise NotFoundException()
        return {'specialityForm': speciality_model(speciality), 'isNew': False, 'saved': saved, 'duplicate': duplicate}

    @Post(value='/specialities', consumes=MediaType.APPLICATION_JSON)
    def create_speciality(self, form: Annotated[SpecialityForm, Body]):
        self.validate(form)
        return HttpResponse.created(speciality_model(self.service.create_speciality(form)))

    @Put(value='/specialities/{id}', consumes=MediaType.APPLICATION_JSON)
    def update_speciality(self, id: int, form: Annotated[SpecialityForm, Body]):
        self.validate(form)
        if form.id is not None and form.id != id:
            domain_error(HttpStatus.BAD_REQUEST, 'Id should match the one in the url')
        return speciality_model(self.service.update_speciality(id, form))
