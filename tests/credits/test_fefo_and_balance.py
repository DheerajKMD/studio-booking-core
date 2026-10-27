from datetime import timedelta

import pytest

from apps.credits import selectors, services
from apps.credits.enums import LedgerReason
from apps.credits.exceptions import InsufficientCredits
from apps.credits.models import LedgerEntry
from tests.conftest import NOW


def test_spends_soonest_expiring_pack_first(member, grant, clock, db):
    late = grant(member, 5, days=60)
    soon = grant(member, 5, days=10)
    services.spend(member, 3, LedgerReason.BOOKING, booking_id=None, clock=clock)
    spent = LedgerEntry.objects.filter(amount__lt=0).get()
    assert spent.pack_id == soon.pk
    assert spent.pack_id != late.pk


def test_spend_spans_packs(member, grant, clock, db):
    soon = grant(member, 2, days=10)
    late = grant(member, 5, days=60)
    services.spend(member, 4, LedgerReason.BOOKING, booking_id=None, clock=clock)
    by_pack = {e.pack_id: e.amount for e in LedgerEntry.objects.filter(amount__lt=0)}
    assert by_pack == {soon.pk: -2, late.pk: -2}
    assert selectors.current_balance(member.pk, clock) == 3


def test_expired_credits_cannot_be_spent(member, grant, clock, db):
    grant(member, 5, days=10)
    clock.set(NOW + timedelta(days=11))
    with pytest.raises(InsufficientCredits):
        services.spend(member, 1, LedgerReason.BOOKING, booking_id=None, clock=clock)


def test_balance_as_of_past_moment(member, grant, clock, db):
    grant(member, 5, days=10)
    before_spend = NOW + timedelta(hours=1)
    clock.set(before_spend)
    services.spend(member, 2, LedgerReason.BOOKING, booking_id=None, clock=clock)
    assert selectors.balance_as_of(member.pk, NOW + timedelta(minutes=30)) == 5
    assert selectors.balance_as_of(member.pk, NOW + timedelta(hours=2)) == 3
    assert selectors.balance_as_of(member.pk, NOW + timedelta(days=11)) == 0


def test_ledger_entries_are_append_only(member, grant, db):
    grant(member, 5)
    entry = LedgerEntry.objects.get()
    entry.amount = 99
    with pytest.raises(RuntimeError):
        entry.save()
    with pytest.raises(RuntimeError):
        entry.delete()
