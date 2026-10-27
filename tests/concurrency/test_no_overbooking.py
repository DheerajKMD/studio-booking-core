import threading
from datetime import timedelta

import pytest
from django.db import connection

from apps.accounts.models import User
from apps.bookings.enums import BookingStatus
from apps.bookings.exceptions import ClassFull
from apps.bookings.models import Booking
from apps.bookings.services.booking import book_class
from apps.credits import selectors
from apps.credits.exceptions import InsufficientCredits
from tests.conftest import NOW


@pytest.mark.django_db(transaction=True)
def test_many_threads_never_overbook(make_member, grant, make_class, clock):
    capacity = 3
    attempts = 12
    session = make_class(NOW + timedelta(days=2), capacity=capacity, cost=2)
    members = [make_member(f"m{i}") for i in range(attempts)]
    for m in members:
        grant(m, 10)

    barrier = threading.Barrier(attempts)
    results: list[str] = []
    lock = threading.Lock()

    def attempt(user: User) -> None:
        try:
            barrier.wait()
            book_class(user, session.pk, clock)
            outcome = "booked"
        except ClassFull:
            outcome = "full"
        except Exception as exc:  # noqa: BLE001
            outcome = f"error:{exc!r}"
        finally:
            connection.close()
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=attempt, args=(m,)) for m in members]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("booked") == capacity
    assert results.count("full") == attempts - capacity
    confirmed = Booking.objects.filter(
        class_session=session, status=BookingStatus.CONFIRMED
    ).count()
    assert confirmed == capacity
    # Only the winners were charged.
    charged = [m for m in members if selectors.current_balance(m.pk, clock) == 8]
    assert len(charged) == capacity


@pytest.mark.django_db(transaction=True)
def test_same_member_double_spend_is_blocked(member, grant, make_class, clock):
    grant(member, 3)  # enough for exactly one class at cost 3
    sessions = [make_class(NOW + timedelta(days=2 + i), cost=3) for i in range(2)]
    barrier = threading.Barrier(2)
    results: list[str] = []
    lock = threading.Lock()

    def attempt(class_id: int) -> None:
        try:
            barrier.wait()
            book_class(member, class_id, clock)
            outcome = "booked"
        except InsufficientCredits:
            outcome = "broke"
        except Exception as exc:  # noqa: BLE001
            outcome = f"error:{exc!r}"
        finally:
            connection.close()
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=attempt, args=(s.pk,)) for s in sessions]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == ["booked", "broke"]
    assert selectors.current_balance(member.pk, clock) == 0