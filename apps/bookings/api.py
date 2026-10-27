from typing import Any

from django.http import HttpRequest
from ninja import Header, Router

from apps.accounts.auth import TokenAuth
from apps.accounts.models import User
from apps.accounts.permissions import ensure_self_or_staff
from apps.common.idempotency import run_idempotent

from . import selectors
from .models import Booking
from .schemas import BookingOut
from .services.booking import book_class

router = Router(tags=["bookings"], auth=TokenAuth())


def to_out(booking: Booking) -> BookingOut:
    return BookingOut(
        id=booking.pk,
        class_id=booking.class_session_id,
        member_id=booking.member_id,
        status=booking.status,
        created_at=booking.created_at,
        cancelled_at=booking.cancelled_at,
    )


@router.post("/classes/{class_id}", response={201: BookingOut})
def book(
    request: HttpRequest,
    class_id: int,
    idempotency_key: str | None = Header(None),
) -> tuple[int, dict[str, Any]]:
    user: User = request.auth  # type: ignore[attr-defined]

    def action() -> tuple[int, dict[str, Any]]:
        booking = book_class(user, class_id)
        return 201, to_out(booking).model_dump(mode="json")

    return run_idempotent(user, idempotency_key, {"class_id": class_id}, action)


@router.get("/members/{member_id}", response=list[BookingOut])
def list_bookings(request: HttpRequest, member_id: int) -> list[BookingOut]:
    ensure_self_or_staff(request.auth, member_id)  # type: ignore[attr-defined]
    return [to_out(b) for b in selectors.member_bookings(member_id)]