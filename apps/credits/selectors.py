from datetime import datetime

from django.db.models import QuerySet, Sum
from django.db.models.functions import Coalesce

from apps.common.clock import Clock, default_clock

from .models import CreditPack, LedgerEntry


def balance_as_of(member_id: int, moment: datetime) -> int:
    """Spendable balance at `moment`: ledger entries up to then,
    on packs that had not yet expired at that moment."""
    total = LedgerEntry.objects.filter(
        member_id=member_id,
        created_at__lte=moment,
        pack__expires_at__gt=moment,
    ).aggregate(s=Sum("amount"))["s"]
    return total or 0


def current_balance(member_id: int, clock: Clock = default_clock) -> int:
    return balance_as_of(member_id, clock.now())


def pack_breakdown(
    member_id: int, clock: Clock = default_clock
) -> QuerySet[CreditPack]:
    """Unexpired packs that still hold credits, soonest expiry first."""
    return (
        CreditPack.objects.filter(member_id=member_id, expires_at__gt=clock.now())
        .annotate(remaining=Coalesce(Sum("entries__amount"), 0))
        .filter(remaining__gt=0)
        .order_by("expires_at", "id")
    )


def movements(member_id: int) -> QuerySet[LedgerEntry]:
    """Every ledger entry for a member, oldest first."""
    return LedgerEntry.objects.filter(member_id=member_id).order_by("created_at", "id")
