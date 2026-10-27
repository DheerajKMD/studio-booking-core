from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Sum

from .models import CreditPack, LedgerEntry


@dataclass(frozen=True)
class Draw:
    pack: CreditPack
    amount: int


class SpendingStrategy(Protocol):
    def plan(
        self, member: AbstractBaseUser, cost: int, now: datetime
    ) -> list[Draw] | None:
        """Return how to pay `cost`, or None if the member can't afford it."""
        ...


class ExpiringSoonestFirst:
    """FEFO: spend credits from the pack that expires soonest."""

    def plan(
        self, member: AbstractBaseUser, cost: int, now: datetime
    ) -> list[Draw] | None:
        packs = (
            CreditPack.objects.select_for_update()
            .filter(member=member, expires_at__gt=now, granted_at__lte=now)
            .order_by("expires_at", "id")
        )
        remaining = cost
        draws: list[Draw] = []
        for pack in packs:
            if remaining == 0:
                break
            left = (
                LedgerEntry.objects.filter(pack=pack).aggregate(s=Sum("amount"))["s"]
                or 0
            )
            take = min(left, remaining)
            if take > 0:
                draws.append(Draw(pack=pack, amount=take))
                remaining -= take
        return draws if remaining == 0 else None
