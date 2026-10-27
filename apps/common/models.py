from django.conf import settings
from django.db import models


class IdempotencyRecord(models.Model):
    key = models.CharField(max_length=200)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
    )
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["member", "key"],
                name="unique_idempotency_key_per_member",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.member_id}:{self.key}"
