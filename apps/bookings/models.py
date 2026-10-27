from django.conf import settings
from django.db import models

from apps.studios.models import ClassSession

from .enums import BookingStatus, WaitlistStatus


class Booking(models.Model):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    class_session = models.ForeignKey(
        ClassSession,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    status = models.CharField(
        max_length=10,
        choices=BookingStatus.choices,
        default=BookingStatus.CONFIRMED,
    )
    created_at = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["member", "class_session"],
                condition=models.Q(status="confirmed"),
                name="one_confirmed_booking_per_member_class",
            ),
        ]

    def __str__(self) -> str:
        return f"Booking {self.pk} ({self.status})"


class WaitlistEntry(models.Model):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="waitlist_entries",
    )
    class_session = models.ForeignKey(
        ClassSession,
        on_delete=models.PROTECT,
        related_name="waitlist_entries",
    )
    status = models.CharField(
        max_length=10,
        choices=WaitlistStatus.choices,
        default=WaitlistStatus.WAITING,
    )
    joined_at = models.DateTimeField()

    class Meta:
        ordering = ["joined_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "class_session"],
                condition=models.Q(status="waiting"),
                name="one_waiting_entry_per_member_class",
            ),
        ]

    def __str__(self) -> str:
        return f"Waitlist {self.pk} ({self.status})"