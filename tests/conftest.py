from datetime import datetime, timedelta, timezone

import pytest

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.common.clock import FixedClock
from apps.credits import services as credit_services
from apps.studios.models import ClassSession, Studio

NOW = datetime(2026, 10, 27, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def staff(db: None) -> User:
    return User.objects.create_user("staff", password="x", role="staff")


@pytest.fixture
def make_member(db: None):
    def _make(name: str) -> User:
        return User.objects.create_user(name, password="x", role="member")

    return _make


@pytest.fixture
def member(make_member) -> User:
    return make_member("alice")


@pytest.fixture
def studio(db: None) -> Studio:
    return Studio.objects.create(
        name="Zen", timezone="Asia/Kolkata", cancellation_cutoff_hours=4
    )


@pytest.fixture
def make_class(studio: Studio):
    def _make(starts_at: datetime, capacity: int = 2, cost: int = 3) -> ClassSession:
        return ClassSession.objects.create(
            studio=studio,
            title="Flow",
            starts_at=starts_at,
            duration_minutes=60,
            capacity=capacity,
            credit_cost=cost,
        )

    return _make


@pytest.fixture
def grant(staff: User, clock: FixedClock):
    def _grant(member: User, credits: int, days: int = 30):
        return credit_services.grant_pack(
            member, staff, credits, NOW + timedelta(days=days), clock
        )

    return _grant