from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

from apps.common.clock import Clock, default_clock
from apps.credits import services as credit_services
from apps.credits.enums import LedgerReason
from apps.credits.exceptions import InsufficientCredits
from apps.studios.models import ClassSession

from ..enums import BookingStatus, WaitlistStatus
from ..exceptions import (
    AlreadyBooked,
    AlreadyWaitlisted,
    ClassAlreadyStarted,
    ClassNotFull,
    WaitlistEntryNotFound,
)
from ..models import Booking, WaitlistEntry
from .booking import confirmed_count, lock_class


def join_waitlist(
    member: AbstractBaseUser, class_id: int, clock: Clock = default_clock
) -> WaitlistEntry:
    now = clock.now()
    with transaction.atomic():
        session = lock_class(class_id)
        if session.starts_at <= now:
            raise ClassAlreadyStarted("This class has already started.")
        if Booking.objects.filter(
            member=member, class_session=session, status=BookingStatus.CONFIRMED
        ).exists():
            raise AlreadyBooked("You already have a spot in this class.")
        if confirmed_count(session) < session.capacity:
            raise ClassNotFull("This class has open spots. Book it directly.")
        if WaitlistEntry.objects.filter(
            member=member, class_session=session, status=WaitlistStatus.WAITING
        ).exists():
            raise AlreadyWaitlisted("You are already on this waitlist.")
        return WaitlistEntry.objects.create(
            member=member, class_session=session, joined_at=now
        )


def leave_waitlist(member_id: int, entry_id: int) -> WaitlistEntry:
    with transaction.atomic():
        entry = (
            WaitlistEntry.objects.select_for_update()
            .filter(pk=entry_id, member_id=member_id)
            .first()
        )
        if entry is None:
            raise WaitlistEntryNotFound(f"Waitlist entry {entry_id} not found.")
        if entry.status == WaitlistStatus.WAITING:
            entry.status = WaitlistStatus.LEFT
            entry.save(update_fields=["status"])
        return entry


def promote_from_waitlist(
    session: ClassSession, clock: Clock = default_clock
) -> list[Booking]:
    """Fill free spots from the waitlist, longest-waiting first.

    Members who can't afford the class are skipped but keep their place.
    Must run inside a transaction that already holds the class row lock.
    """
    now = clock.now()
    promoted: list[Booking] = []
    if session.starts_at <= now:
        return promoted

    free = session.capacity - confirmed_count(session)
    if free <= 0:
        return promoted

    waiting = (
        WaitlistEntry.objects.select_for_update()
        .filter(class_session=session, status=WaitlistStatus.WAITING)
        .order_by("joined_at", "id")
    )
    for entry in waiting:
        if free <= 0:
            break

        already_booked = Booking.objects.filter(
            member_id=entry.member_id,
            class_session=session,
            status=BookingStatus.CONFIRMED,
        ).exists()
        if already_booked:
            entry.status = WaitlistStatus.LEFT
            entry.save(update_fields=["status"])
            continue

        try:
            with transaction.atomic():  # savepoint: undo the booking if unaffordable
                booking = Booking.objects.create(
                    member_id=entry.member_id,
                    class_session=session,
                    status=BookingStatus.CONFIRMED,
                    created_at=now,
                )
                credit_services.spend(
                    entry.member,
                    session.credit_cost,
                    LedgerReason.WAITLIST_CHARGE,
                    booking_id=booking.pk,
                    clock=clock,
                )
        except InsufficientCredits:
            continue  # keeps their place in line

        entry.status = WaitlistStatus.PROMOTED
        entry.save(update_fields=["status"])
        promoted.append(booking)
        free -= 1
    return promoted
