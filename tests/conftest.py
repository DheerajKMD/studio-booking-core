from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from apps.accounts.models import User
from apps.common.clock import FixedClock
from apps.credits import services as credit_services
from apps.credits.models import CreditPack
from apps.studios.models import ClassSession, Studio

NOW = datetime(2026, 10, 27, 10, 0, tzinfo=UTC)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def staff(db: None) -> User:
    user: User = User.objects.create_user("staff", password="x", role="staff")
    return user


@pytest.fixture
def make_member(db: None) -> Callable[[str], User]:
    def _make(name: str) -> User:
        user: User = User.objects.create_user(name, password="x", role="member")
        return user

    return _make


@pytest.fixture
def member(make_member: Callable[[str], User]) -> User:
    return make_member("alice")


@pytest.fixture
def studio(db: None) -> Studio:
    return Studio.objects.create(
        name="Zen", timezone="Asia/Kolkata", cancellation_cutoff_hours=4
    )


@pytest.fixture
def make_class(studio: Studio) -> Callable[..., ClassSession]:
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
def grant(staff: User, clock: FixedClock) -> Callable[..., CreditPack]:
    def _grant(member: User, credits: int, days: int = 30) -> CreditPack:
        return credit_services.grant_pack(
            member, staff, credits, NOW + timedelta(days=days), clock
        )

    return _grant
