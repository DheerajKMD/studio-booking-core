from django.db import models


class BookingStatus(models.TextChoices):
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"


class WaitlistStatus(models.TextChoices):
    WAITING = "waiting", "Waiting"
    PROMOTED = "promoted", "Promoted"
    LEFT = "left", "Left"