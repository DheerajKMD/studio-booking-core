from typing import Any

from django.http import HttpRequest
from ninja import Header, Router

from apps.accounts.auth import TokenAuth
from apps.accounts.models import User
from apps.accounts.permissions import ensure_self_or_staff
from apps.common.idempotency import run_idempotent

from . import selectors
from .models import Booking, WaitlistEntry
from .schemas import BookingOut, WaitlistOut
from .services.booking import book_class
from .services.cancellation import cancel_booking
from .services.waitlist import join_waitlist, leave_waitlist

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


def waitlist_out(entry: WaitlistEntry) -> WaitlistOut:
    return WaitlistOut(
        id=entry.pk,
        class_id=entry.class_session_id,
        member_id=entry.member_id,
        status=entry.status,
        joined_at=entry.joined_at,
    )


@router.post("/{booking_id}/cancel", response=BookingOut)
def cancel(request: HttpRequest, booking_id: int) -> BookingOut:
    user: User = request.auth  # type: ignore[attr-defined]
    member_id = None if user.is_studio_staff else user.pk
    return to_out(cancel_booking(booking_id, member_id))


@router.post("/classes/{class_id}/waitlist", response={201: WaitlistOut})
def join(request: HttpRequest, class_id: int) -> tuple[int, WaitlistOut]:
    entry = join_waitlist(request.auth, class_id)  # type: ignore[attr-defined]
    return 201, waitlist_out(entry)


@router.delete("/waitlist/{entry_id}", response=WaitlistOut)
def leave(request: HttpRequest, entry_id: int) -> WaitlistOut:
    user: User = request.auth  # type: ignore[attr-defined]
    return waitlist_out(leave_waitlist(user.pk, entry_id))


@router.get("/members/{member_id}/waitlist", response=list[WaitlistOut])
def list_waitlist(request: HttpRequest, member_id: int) -> list[WaitlistOut]:
    ensure_self_or_staff(request.auth, member_id)  # type: ignore[attr-defined]
    return [waitlist_out(e) for e in selectors.member_waitlist(member_id)]
