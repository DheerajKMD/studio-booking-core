import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STAFF = "staff", "Staff"
        MEMBER = "member", "Member"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    @property
    def is_studio_staff(self) -> bool:
        return self.role == self.Role.STAFF


def generate_token_key() -> str:
    return secrets.token_hex(20)


class AuthToken(models.Model):
    key = models.CharField(
        max_length=40,
        primary_key=True,
        default=generate_token_key,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="auth_tokens",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Token for {self.user_id}"
