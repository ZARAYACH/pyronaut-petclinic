"""Oracle's competing LOW and HIGH appointment transactions from the reference."""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Protocol

from jakarta.inject import Inject, Singleton
from jakarta.validation.constraints import NotBlank, NotNull
from java.lang import RuntimeException
from micronaut.context.annotation import Requires, Value
from micronaut.data.annotation import GeneratedValue, Id, MappedEntity, MappedProperty, Query
from micronaut.data.exceptions import DataAccessException
from micronaut.data.repository import GenericRepository
from micronaut.http import HttpRequest, HttpResponse, HttpStatus, MediaType
from micronaut.http.annotation import Controller, Error, Get, Post, Produces, QueryValue
from micronaut.http.exceptions import HttpStatusException
from micronaut.scheduling.annotation import ExecuteOn
from micronaut.serde.annotation import Serdeable
from micronaut.transaction.annotation import OracleTransactional, Transactional
from micronaut.transaction.exceptions import OracleTransactionPriorityException, TransactionTimedOutException
from micronaut.views import View

LOG = logging.getLogger(__name__)


class AppointmentStatus(Enum):
    AVAILABLE = 'AVAILABLE'
    HELD_BY_REGULAR = 'HELD_BY_REGULAR'
    BOOKED_FOR_REGULAR = 'BOOKED_FOR_REGULAR'
    BOOKED_FOR_EMERGENCY = 'BOOKED_FOR_EMERGENCY'


class BookingType(Enum):
    REGULAR = 'REGULAR'
    EMERGENCY = 'EMERGENCY'


class BookingOutcome(Enum):
    COMMITTED = 'COMMITTED'
    PRIORITY_ROLLED_BACK = 'PRIORITY_ROLLED_BACK'
    TAKEN = 'TAKEN'
    TIMED_OUT = 'TIMED_OUT'
    FAILED = 'FAILED'


@Serdeable
@MappedEntity('APPOINTMENTS')
@dataclass
class Appointment:
    label: Annotated[str, NotBlank, MappedProperty("LABEL")]
    displayOrder: Annotated[int, NotNull, MappedProperty("DISPLAY_ORDER")]
    status: Annotated[AppointmentStatus, NotNull, MappedProperty("STATUS")] = AppointmentStatus.AVAILABLE
    id: Annotated[int | None, Id, GeneratedValue] = None


class AppointmentRepository(GenericRepository[Appointment, int], Protocol):
    @Query(value='SELECT a.* FROM APPOINTMENTS a WHERE a.ID = :appointmentId FOR UPDATE WAIT 10', nativeQuery=True)
    def findByIdForUpdate(self, appointmentId: int) -> Appointment | None: ...

    @Query(value="SELECT a.* FROM APPOINTMENTS a WHERE STATUS = 'AVAILABLE' ORDER BY DISPLAY_ORDER, ID", nativeQuery=True)
    def findAvailableAppointments(self) -> list[Appointment]: ...

    def findOneById(self, id: int) -> Appointment | None: ...


class BookingTaken(RuntimeError):
    pass


def status_name(value) -> str:
    if isinstance(value, AppointmentStatus):
        return value.value
    name = value.name
    return str(name() if callable(name) else name)


def with_status(appointment, status: AppointmentStatus) -> Appointment:
    # Repository results may be Java mirrors rather than native dataclasses.
    return Appointment(label=appointment.label, displayOrder=appointment.displayOrder,
                       status=status, id=appointment.id)


def appointment_model(appointment) -> dict:
    return {'id': appointment.id, 'label': appointment.label, 'displayOrder': appointment.displayOrder,
            'status': status_name(appointment.status)}


@Singleton
@Requires(env=['oracle'])
class OracleTransactionPriorityService:
    appointments: Annotated[AppointmentRepository, Inject]
    reservationSeconds: Annotated[int, Value('${petclinic.transaction-priority.reservation-seconds:15}')]

    def get_reservation_seconds(self) -> int:
        return self.reservationSeconds

    def lock_available(self, appointment_id: int) -> Appointment:
        appointment = self.appointments.findByIdForUpdate(appointment_id)
        if appointment is None or status_name(appointment.status) != 'AVAILABLE':
            raise BookingTaken('The appointment has already been booked')
        return appointment

    @OracleTransactional(priority=OracleTransactional.Priority.LOW, timeout=30)
    def book_regular(self, appointment_id: int) -> None:
        appointment = self.lock_available(appointment_id)
        appointment = self.appointments.save(with_status(appointment, AppointmentStatus.HELD_BY_REGULAR))
        time.sleep(self.reservationSeconds)
        self.appointments.save(with_status(appointment, AppointmentStatus.BOOKED_FOR_REGULAR))

    @OracleTransactional(priority=OracleTransactional.Priority.HIGH, timeout=30)
    def book_emergency(self, appointment_id: int) -> None:
        appointment = self.lock_available(appointment_id)
        self.appointments.save(with_status(appointment, AppointmentStatus.BOOKED_FOR_EMERGENCY))

    @Transactional
    def reset_fixture(self) -> None:
        for appointment in self.appointments.findAll():
            self.appointments.save(with_status(appointment, AppointmentStatus.AVAILABLE))


@Serdeable
@dataclass
class OracleBookingResult:
    appointmentId: int
    outcome: BookingOutcome
    databaseStatus: AppointmentStatus
    availableAppointments: list[Appointment]


def booking_outcome(error) -> BookingOutcome:
    if isinstance(error, OracleTransactionPriorityException):
        return BookingOutcome.PRIORITY_ROLLED_BACK
    if isinstance(error, BookingTaken):
        return BookingOutcome.TAKEN
    if isinstance(error, TransactionTimedOutException):
        return BookingOutcome.TIMED_OUT
    if isinstance(error, DataAccessException):
        cause = error.getCause()
        if cause is not None and hasattr(cause, 'getErrorCode') and cause.getErrorCode() in (54, 30006, 1013):
            return BookingOutcome.TIMED_OUT
    return BookingOutcome.FAILED


@Controller('/oracle/transaction-priority')
@Requires(env=['oracle'])
@ExecuteOn('blocking')
class OracleTransactionPriorityController:
    service: Annotated[OracleTransactionPriorityService, Inject]
    appointments: Annotated[AppointmentRepository, Inject]

    @Get
    @View('transaction-priority/showcase')
    @Produces(MediaType.TEXT_HTML)
    def page(self) -> dict:
        return {'appointments': [appointment_model(a) for a in self.appointments.findAvailableAppointments()],
                'reservationSeconds': self.service.get_reservation_seconds()}

    @Post('/reset')
    def reset(self) -> dict:
        try:
            self.service.reset_fixture()
        except (RuntimeException, Exception) as error:
            if booking_outcome(error) == BookingOutcome.TIMED_OUT:
                raise HttpStatusException(HttpStatus.CONFLICT, 'A booking is still running. Wait for it to finish before resetting.')
            raise
        return {'status': 'reset'}

    @Post('/book')
    def book(self, appointmentId: Annotated[int, QueryValue], type: Annotated[str, QueryValue]):
        try:
            booking_type = BookingType(type.upper())
        except ValueError:
            raise HttpStatusException(HttpStatus.BAD_REQUEST, 'Invalid booking type.')
        if not self.appointments.existsById(appointmentId):
            raise HttpStatusException(HttpStatus.NOT_FOUND, 'Appointment not found.')
        outcome = BookingOutcome.COMMITTED
        try:
            if booking_type == BookingType.REGULAR:
                self.service.book_regular(appointmentId)
            else:
                self.service.book_emergency(appointmentId)
        except (RuntimeException, Exception) as error:
            outcome = booking_outcome(error)
            if outcome == BookingOutcome.FAILED:
                LOG.error('Appointment booking failed for appointmentId=%s: %s', appointmentId, error)
        booked = self.appointments.findOneById(appointmentId)
        if booked is None:
            raise HttpStatusException(HttpStatus.NOT_FOUND, 'Appointment not found.')
        status = {BookingOutcome.COMMITTED: HttpStatus.OK, BookingOutcome.PRIORITY_ROLLED_BACK: HttpStatus.CONFLICT,
                  BookingOutcome.TAKEN: HttpStatus.CONFLICT, BookingOutcome.TIMED_OUT: HttpStatus.SERVICE_UNAVAILABLE,
                  BookingOutcome.FAILED: HttpStatus.INTERNAL_SERVER_ERROR}[outcome]
        return HttpResponse.status(status).body(OracleBookingResult(appointmentId, outcome, AppointmentStatus(status_name(booked.status)),
                                                                    [with_status(a, AppointmentStatus(status_name(a.status))) for a in self.appointments.findAvailableAppointments()]))

    @Error(exception=HttpStatusException)
    def lab_error(self, request: HttpRequest, error: HttpStatusException):
        body = {'message': error.getMessage()}
        if error.getStatus() == HttpStatus.NOT_FOUND:
            body['path'] = request.getPath()
        return HttpResponse.status(error.getStatus()).body(body)
