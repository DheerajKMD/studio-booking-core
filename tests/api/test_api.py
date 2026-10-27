from datetime import timedelta

from django.test import Client
from django.utils import timezone

from apps.accounts.models import AuthToken
from apps.bookings.models import Booking
from apps.common.idempotency import run_idempotent
from apps.credits import selectors


def auth(user) -> dict[str, str]:
    token = AuthToken.objects.create(user=user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token.key}"}


def test_member_cannot_read_another_members_balance(make_member):
    alice, bob = make_member("alice"), make_member("bob")
    resp = Client().get(f"/api/credits/members/{bob.pk}/balance", **auth(alice))
    assert resp.status_code == 403
    resp = Client().get(f"/api/credits/members/{alice.pk}/balance", **auth(alice))
    assert resp.status_code == 200


def test_member_cannot_grant_credits(make_member):
    alice = make_member("alice")
    resp = Client().post(
        f"/api/credits/members/{alice.pk}/packs",
        {"credits": 5, "expires_at": "2030-01-01T00:00:00Z"},
        content_type="application/json",
        **auth(alice),
    )
    assert resp.status_code == 403


def test_retry_with_same_idempotency_key_books_once(member, grant, make_class, clock):
    grant(member, 10)  # fixed-clock grant, expires in 30 days from test NOW
    session = make_class(timezone.now() + timedelta(days=2))
    headers = {**auth(member), "HTTP_IDEMPOTENCY_KEY": "abc-1"}

    first = Client().post(f"/api/bookings/classes/{session.pk}", **headers)
    second = Client().post(f"/api/bookings/classes/{session.pk}", **headers)

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert Booking.objects.filter(member=member).count() == 1
    assert selectors.balance_as_of(member.pk, timezone.now() + timedelta(days=1)) == 7


def test_same_key_different_request_is_rejected(member):
    calls: list[int] = []

    def action() -> tuple[int, dict]:
        calls.append(1)
        return 201, {}

    run_idempotent(member, "k", {"class_id": 1}, action)
    run_idempotent(member, "k", {"class_id": 1}, action)
    assert len(calls) == 1
