"""Oracle's competing LOW and HIGH appointment transactions from the reference."""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Protocol
from jakarta.inject import Inject, Singleton
from jakarta.validation.constraints import NotBlank, NotNull
from micronaut.context.annotation import Requires, Value
from micronaut.data.annotation import GeneratedValue, Id, MappedEntity, MappedProperty, Query
from micronaut.data.repository import GenericRepository
from micronaut.serde.annotation import Serdeable
from micronaut.transaction.annotation import OracleTransactional, Transactional


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
