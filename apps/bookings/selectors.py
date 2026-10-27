from django.db.models import QuerySet

from .models import Booking


def member_bookings(member_id: int) -> QuerySet[Booking]:
    return Booking.objects.filter(member_id=member_id).order_by("-created_at", "-id")