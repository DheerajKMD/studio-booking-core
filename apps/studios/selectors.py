from datetime import datetime

from django.db.models import Count, F, Q, QuerySet

from .models import ClassSession


def classes_in_range(
    start: datetime,
    end: datetime,
    studio_id: int | None = None,
) -> QuerySet[ClassSession]:
    qs = ClassSession.objects.filter(starts_at__gte=start, starts_at__lt=end)
    if studio_id is not None:
        qs = qs.filter(studio_id=studio_id)
    return qs.annotate(
        confirmed_count=Count("bookings", filter=Q(bookings__status="confirmed")),
        spots_available=F("capacity") - F("confirmed_count"),
    ).order_by("starts_at")
