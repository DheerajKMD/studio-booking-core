from typing import Any

from django.core.management.base import BaseCommand

from apps.accounts.models import User

PASSWORD = "pass1234"

DEMO_USERS = [
    ("meera", User.Role.STAFF),
    ("arjun", User.Role.MEMBER),
    ("divya", User.Role.MEMBER),
    ("rahul", User.Role.MEMBER),
]


class Command(BaseCommand):
    help = "Create the demo staff user and three demo members (safe to re-run)."

    def handle(self, *args: Any, **options: Any) -> None:
        for username, role in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={"role": role}
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            state = "created" if created else "already exists"
            self.stdout.write(f"{username} ({role}): {state}")
        self.stdout.write(self.style.SUCCESS(f"Done. Password for all: {PASSWORD}"))
