from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

from apps.common.clock import Clock, default_clock

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