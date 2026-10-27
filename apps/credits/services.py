from datetime import datetime

from django.db import transaction

from apps.accounts.models import User
from apps.common.clock import Clock, default_clock

from .enums import LedgerReason
from .exceptions import InsufficientCredits, InvalidPack
from .models import CreditPack, LedgerEntry
from .spending import Draw, ExpiringSoonestFirst, SpendingStrategy

strategy: SpendingStrategy = ExpiringSoonestFirst()


def grant_pack(
    member: User,
    granted_by: User,
    credits: int,
    expires_at: datetime,
    clock: Clock = default_clock,
) -> CreditPack:
    now = clock.now()
    if credits <= 0:
        raise InvalidPack("Credits must be a positive whole number.")
    if expires_at <= now:
        raise InvalidPack("Expiry must be in the future.")
    with transaction.atomic():
        pack = CreditPack.objects.create(
            member=member,
            credits=credits,
            granted_at=now,
            expires_at=expires_at,
            granted_by=granted_by,
        )
        LedgerEntry.objects.create(
            member=member,
            pack=pack,
            amount=credits,
            reason=LedgerReason.GRANT,
            created_at=now,
        )
    return pack


def can_afford(member: User, cost: int, clock: Clock = default_clock) -> bool:
    """Call inside a transaction (it locks pack rows)."""
    return strategy.plan(member, cost, clock.now()) is not None


def spend(
    member: User,
    cost: int,
    reason: LedgerReason,
    booking_id: int | None,
    clock: Clock = default_clock,
) -> list[Draw]:
    """Charge `cost` credits, soonest-expiring first. Must run inside a transaction."""
    now = clock.now()
    draws = strategy.plan(member, cost, now)
    if draws is None:
        raise InsufficientCredits("Not enough unexpired credits.")
    for draw in draws:
        LedgerEntry.objects.create(
            member=member,
            pack=draw.pack,
            amount=-draw.amount,
            reason=reason,
            booking_id=booking_id,
            created_at=now,
        )
    return draws


def refund_booking(booking_id: int, clock: Clock = default_clock) -> int:
    """Return a booking's credits to the packs they came from.

    Safe to call twice: a second call finds the earlier refund and does nothing.
    Must run inside a transaction. Returns the number of credits refunded.
    """
    already_refunded = LedgerEntry.objects.filter(
        booking_id=booking_id, reason=LedgerReason.REFUND
    ).exists()
    if already_refunded:
        return 0

    now = clock.now()
    charges = LedgerEntry.objects.filter(booking_id=booking_id, amount__lt=0)
    total = 0
    for charge in charges:
        LedgerEntry.objects.create(
            member_id=charge.member_id,
            pack_id=charge.pack_id,
            amount=-charge.amount,
            reason=LedgerReason.REFUND,
            booking_id=booking_id,
            created_at=now,
        )
        total += -charge.amount
    return total
