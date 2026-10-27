from django.db import transaction

from apps.accounts.models import User
from apps.common.clock import Clock, default_clock
from apps.credits import services as credit_services
from apps.credits.enums import LedgerReason
from apps.studios.models import ClassSession

from ..enums import BookingStatus
from ..exceptions import AlreadyBooked, ClassAlreadyStarted, ClassFull, ClassNotFound
from ..models import Booking


def lock_class(class_id: int) -> ClassSession:
    """Lock the class row. Call inside a transaction."""
    try:
        return (
            ClassSession.objects.select_for_update()
            .select_related("studio")
            .get(pk=class_id)
        )
    except ClassSession.DoesNotExist:
        raise ClassNotFound(f"Class {class_id} not found.") from None


def confirmed_count(class_session: ClassSession) -> int:
    return Booking.objects.filter(
        class_session=class_session, status=BookingStatus.CONFIRMED
    ).count()


def book_class(
    member: User,
    class_id: int,
    clock: Clock = default_clock,
) -> Booking:
    now = clock.now()
    with transaction.atomic():
        session = lock_class(class_id)
        if session.starts_at <= now:
            raise ClassAlreadyStarted("This class has already started.")
        if Booking.objects.filter(
            member=member,
            class_session=session,
            status=BookingStatus.CONFIRMED,
        ).exists():
            raise AlreadyBooked("You already have a spot in this class.")
        if confirmed_count(session) >= session.capacity:
            raise ClassFull("This class is full.")

        booking = Booking.objects.create(
            member=member,
            class_session=session,
            status=BookingStatus.CONFIRMED,
            created_at=now,
        )
        credit_services.spend(
            member,
            session.credit_cost,
            LedgerReason.BOOKING,
            booking_id=booking.pk,
            clock=clock,
        )
        return booking
