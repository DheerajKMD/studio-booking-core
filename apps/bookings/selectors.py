from django.db.models import QuerySet

from .models import Booking
from .models import WaitlistEntry


def member_bookings(member_id: int) -> QuerySet[Booking]:
    return Booking.objects.filter(member_id=member_id).order_by("-created_at", "-id")




def member_waitlist(member_id: int) -> QuerySet[WaitlistEntry]:
    return WaitlistEntry.objects.filter(member_id=member_id).order_by("-joined_at", "-id")