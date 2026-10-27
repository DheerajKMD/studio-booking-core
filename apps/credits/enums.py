from django.db import models


class LedgerReason(models.TextChoices):
    GRANT = "grant", "Pack granted"
    BOOKING = "booking", "Booking charge"
    WAITLIST_CHARGE = "waitlist_charge", "Waitlist promotion charge"
    REFUND = "refund", "Cancellation refund"
