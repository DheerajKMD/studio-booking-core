from datetime import datetime

from ninja import Schema
from pydantic import Field


class GrantIn(Schema):
    credits: int = Field(gt=0)
    expires_at: datetime


class PackOut(Schema):
    id: int
    credits: int
    granted_at: datetime
    expires_at: datetime


class PackBalanceOut(Schema):
    id: int
    remaining: int
    expires_at: datetime


class BalanceOut(Schema):
    member_id: int
    balance: int
    as_of: datetime | None = None
    packs: list[PackBalanceOut] = []


class MovementOut(Schema):
    id: int
    pack_id: int
    amount: int
    reason: str
    booking_id: int | None
    created_at: datetime
