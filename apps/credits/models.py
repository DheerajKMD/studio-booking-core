from django.conf import settings
from django.db import models

from .enums import LedgerReason


class CreditPack(models.Model):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="credit_packs",
    )
    credits = models.PositiveIntegerField()
    granted_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(credits__gt=0),
                name="pack_credits_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F("granted_at")),
                name="pack_expiry_after_grant",
            ),
        ]

    def __str__(self) -> str:
        return f"Pack {self.pk}: {self.credits} credits"


class LedgerEntry(models.Model):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )
    pack = models.ForeignKey(
        CreditPack,
        on_delete=models.PROTECT,
        related_name="entries",
    )
    amount = models.IntegerField()
    reason = models.CharField(max_length=20, choices=LedgerReason.choices)
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )
    created_at = models.DateTimeField(db_index=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(amount=0),
                name="ledger_amount_nonzero",
            ),
        ]
        indexes = [
            models.Index(fields=["member", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Ledger {self.pk}: {self.amount} ({self.reason})"

    def save(self, *args: object, **kwargs: object) -> None:
        if self.pk is not None:
            raise RuntimeError("Ledger entries are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args: object, **kwargs: object) -> tuple[int, dict[str, int]]:
        raise RuntimeError("Ledger entries are append-only.")
