from datetime import datetime

from django.http import HttpRequest
from ninja import Router

from apps.accounts.auth import TokenAuth
from apps.accounts.models import User
from apps.accounts.permissions import ensure_self_or_staff, require_staff
from apps.common.clock import default_clock
from apps.common.exceptions import DomainError

from . import selectors, services
from .schemas import BalanceOut, GrantIn, MovementOut, PackBalanceOut, PackOut

router = Router(tags=["credits"], auth=TokenAuth())


class MemberNotFound(DomainError):
    status_code = 404
    code = "member_not_found"


@router.post("/members/{member_id}/packs", response={201: PackOut})
def grant_pack(
    request: HttpRequest, member_id: int, payload: GrantIn
) -> tuple[int, PackOut]:
    require_staff(request.auth)  # type: ignore[attr-defined]
    member = User.objects.filter(pk=member_id, role=User.Role.MEMBER).first()
    if member is None:
        raise MemberNotFound(f"Member {member_id} not found.")
    pack = services.grant_pack(
        member, request.auth, payload.credits, payload.expires_at  # type: ignore[attr-defined]
    )
    return 201, PackOut(
        id=pack.pk,
        credits=pack.credits,
        granted_at=pack.granted_at,
        expires_at=pack.expires_at,
    )


@router.get("/members/{member_id}/balance", response=BalanceOut)
def balance(
    request: HttpRequest, member_id: int, as_of: datetime | None = None
) -> BalanceOut:
    ensure_self_or_staff(request.auth, member_id)  # type: ignore[attr-defined]
    if as_of is not None:
        return BalanceOut(
            member_id=member_id,
            balance=selectors.balance_as_of(member_id, as_of),
            as_of=as_of,
        )
    packs = [
        PackBalanceOut(id=p.pk, remaining=p.remaining, expires_at=p.expires_at)  # type: ignore[attr-defined]
        for p in selectors.pack_breakdown(member_id)
    ]
    return BalanceOut(
        member_id=member_id,
        balance=selectors.current_balance(member_id),
        as_of=default_clock.now(),
        packs=packs,
    )


@router.get("/members/{member_id}/movements", response=list[MovementOut])
def movements(request: HttpRequest, member_id: int) -> list[MovementOut]:
    ensure_self_or_staff(request.auth, member_id)  # type: ignore[attr-defined]
    return [
        MovementOut(
            id=e.pk,
            pack_id=e.pack_id,
            amount=e.amount,
            reason=e.reason,
            booking_id=e.booking_id,
            created_at=e.created_at,
        )
        for e in selectors.movements(member_id)
    ]