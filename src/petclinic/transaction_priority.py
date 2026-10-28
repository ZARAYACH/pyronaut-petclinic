"""Oracle's competing LOW and HIGH appointment transactions from the reference."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Protocol
from jakarta.validation.constraints import NotBlank, NotNull
from micronaut.data.annotation import GeneratedValue, Id, MappedEntity, MappedProperty, Query
from micronaut.data.repository import GenericRepository
from micronaut.serde.annotation import Serdeable


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


@Serdeable
@dataclass
class OracleBookingResult:
    appointmentId: int
    outcome: BookingOutcome
    databaseStatus: AppointmentStatus
    availableAppointments: list[Appointment]
