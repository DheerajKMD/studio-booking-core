from django.db import transaction

from apps.common.clock import Clock, default_clock
from apps.credits import services as credit_services

from ..cancellation_policy import is_refundable
from ..enums import BookingStatus
from ..exceptions import BookingNotFound, ClassAlreadyStarted
from ..models import Booking
from .booking import lock_class
from .waitlist import promote_from_waitlist

def cancel_booking(
    booking_id: int,
    member_id: int | None = None,
    clock: Clock = default_clock,
) -> Booking:
    """Cancel a booking. `member_id` restricts it to that member's own booking."""
    now = clock.now()
    with transaction.atomic():
        found = (
            Booking.objects.filter(pk=booking_id)
            .values_list("class_session_id", flat=True)
            .first()
        )
        if found is None:
            raise BookingNotFound(f"Booking {booking_id} not found.")

        # Lock the class first, then the booking: same order as booking.
        session = lock_class(found)
        booking = Booking.objects.select_for_update().get(pk=booking_id)

        if member_id is not None and booking.member_id != member_id:
            raise BookingNotFound(f"Booking {booking_id} not found.")

        if booking.status == BookingStatus.CANCELLED:
            return booking

        if session.starts_at <= now:
            raise ClassAlreadyStarted("This class has already started.")

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = now
        booking.save(update_fields=["status", "cancelled_at"])

        if is_refundable(session, now):
            credit_services.refund_booking(booking.pk, clock=clock)
        # Late cancel: no ledger entry. The original charge stays final.

        promote_from_waitlist(session, clock)
        return booking

