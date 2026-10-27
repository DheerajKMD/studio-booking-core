from datetime import datetime, timedelta, timezone

import pytest

from apps.bookings.cancellation_policy import is_refundable
from apps.bookings.enums import WaitlistStatus
from apps.bookings.exceptions import BookingNotFound, ClassFull
from apps.bookings.models import WaitlistEntry
from apps.bookings.services.booking import book_class
from apps.bookings.services.cancellation import cancel_booking
from apps.bookings.services.waitlist import join_waitlist
from apps.credits import selectors
from apps.credits.enums import LedgerReason
from apps.credits.models import LedgerEntry
from apps.studios.models import ClassSession, Studio
from tests.conftest import NOW


def test_booking_charges_class_cost(member, grant, make_class, clock):
    grant(member, 10)
    book_class(member, make_class(NOW + timedelta(days=2)).pk, clock)
    assert selectors.current_balance(member.pk, clock) == 7


def test_full_class_rejects_booking(make_member, grant, make_class, clock):
    a, b = make_member("a"), make_member("b")
    grant(a, 10)
    grant(b, 10)
    session = make_class(NOW + timedelta(days=2), capacity=1)
    book_class(a, session.pk, clock)
    with pytest.raises(ClassFull):
        book_class(b, session.pk, clock)


def test_cancel_before_cutoff_refunds(member, grant, make_class, clock):
    grant(member, 10)
    booking = book_class(member, make_class(NOW + timedelta(days=2)).pk, clock)
    cancel_booking(booking.pk, member.pk, clock)
    assert selectors.current_balance(member.pk, clock) == 10


def test_cancel_after_cutoff_forfeits(member, grant, make_class, clock):
    grant(member, 10)
    # starts in 3h, cutoff is 4h -> already past the cutoff
    booking = book_class(member, make_class(NOW + timedelta(hours=3)).pk, clock)
    cancel_booking(booking.pk, member.pk, clock)
    assert selectors.current_balance(member.pk, clock) == 7


def test_cancel_exactly_at_cutoff_refunds(member, grant, make_class, clock):
    grant(member, 10)
    booking = book_class(member, make_class(NOW + timedelta(hours=4)).pk, clock)
    cancel_booking(booking.pk, member.pk, clock)
    assert selectors.current_balance(member.pk, clock) == 10


def test_cutoff_is_measured_in_studio_local_time(db):
    # New York clocks go back on 2026-11-01. Class at 04:00 EST (09:00 UTC).
    # 4 hours before in local wall-clock time is 00:00 EDT = 04:00 UTC.
    studio = Studio.objects.create(
        name="NY", timezone="America/New_York", cancellation_cutoff_hours=4
    )
    session = ClassSession.objects.create(
        studio=studio,
        title="Flow",
        starts_at=datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc),
        duration_minutes=60,
        capacity=5,
        credit_cost=1,
    )
    assert is_refundable(session, datetime(2026, 11, 1, 3, 59, tzinfo=timezone.utc))
    assert not is_refundable(session, datetime(2026, 11, 1, 4, 30, tzinfo=timezone.utc))


def test_double_cancel_refunds_once(member, grant, make_class, clock):
    grant(member, 10)
    booking = book_class(member, make_class(NOW + timedelta(days=2)).pk, clock)
    cancel_booking(booking.pk, member.pk, clock)
    cancel_booking(booking.pk, member.pk, clock)
    assert selectors.current_balance(member.pk, clock) == 10
    refunds = LedgerEntry.objects.filter(reason=LedgerReason.REFUND)
    assert refunds.count() == 1


def test_member_cannot_cancel_someone_elses_booking(
    make_member, grant, make_class, clock
):
    a, b = make_member("a"), make_member("b")
    grant(a, 10)
    booking = book_class(a, make_class(NOW + timedelta(days=2)).pk, clock)
    with pytest.raises(BookingNotFound):
        cancel_booking(booking.pk, b.pk, clock)


def test_waitlist_skips_unaffordable_member_and_keeps_their_place(
    make_member, grant, make_class, clock
):
    holder, broke, rich = make_member("h"), make_member("broke"), make_member("rich")
    grant(holder, 10)
    grant(rich, 10)
    session = make_class(NOW + timedelta(days=2), capacity=1)
    booking = book_class(holder, session.pk, clock)
    join_waitlist(broke, session.pk, clock)
    clock.set(NOW + timedelta(minutes=1))
    join_waitlist(rich, session.pk, clock)
    clock.set(NOW)

    cancel_booking(booking.pk, holder.pk, clock)

    status = {e.member.username: e.status for e in WaitlistEntry.objects.all()}
    assert status == {
        "broke": WaitlistStatus.WAITING,
        "rich": WaitlistStatus.PROMOTED,
    }
    assert selectors.current_balance(rich.pk, clock) == 7