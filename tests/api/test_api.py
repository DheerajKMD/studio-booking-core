from datetime import timedelta
from typing import Any

from django.test import Client
from django.utils import timezone

from apps.accounts.models import AuthToken, User
from apps.bookings.models import Booking
from apps.common.idempotency import run_idempotent
from apps.credits import selectors


def bearer(user: User) -> str:
    token = AuthToken.objects.create(user=user)
    return f"Bearer {token.key}"


def test_member_cannot_read_another_members_balance(make_member: Any) -> None:
    alice, bob = make_member("alice"), make_member("bob")
    resp = Client().get(
        f"/api/credits/members/{bob.pk}/balance",
        headers={"Authorization": bearer(alice)},
    )
    assert resp.status_code == 403
    resp = Client().get(
        f"/api/credits/members/{alice.pk}/balance",
        headers={"Authorization": bearer(alice)},
    )
    assert resp.status_code == 200


def test_member_cannot_grant_credits(make_member: Any) -> None:
    alice = make_member("alice")
    resp = Client().post(
        f"/api/credits/members/{alice.pk}/packs",
        {"credits": 5, "expires_at": "2030-01-01T00:00:00Z"},
        content_type="application/json",
        headers={"Authorization": bearer(alice)},
    )
    assert resp.status_code == 403


def test_retry_with_same_idempotency_key_books_once(
    member: User, grant: Any, make_class: Any, clock: Any
) -> None:
    grant(member, 10)
    session = make_class(timezone.now() + timedelta(days=2))
    headers = {"Authorization": bearer(member), "Idempotency-Key": "abc-1"}

    first = Client().post(f"/api/bookings/classes/{session.pk}", headers=headers)
    second = Client().post(f"/api/bookings/classes/{session.pk}", headers=headers)

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert Booking.objects.filter(member=member).count() == 1
    assert selectors.balance_as_of(member.pk, timezone.now() + timedelta(days=1)) == 7


def test_same_key_same_request_runs_action_once(member: User) -> None:
    calls: list[int] = []

    def action() -> tuple[int, dict[str, Any]]:
        calls.append(1)
        return 201, {}

    run_idempotent(member, "k", {"class_id": 1}, action)
    run_idempotent(member, "k", {"class_id": 1}, action)
    assert len(calls) == 1
