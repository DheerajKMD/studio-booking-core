from datetime import datetime

from ninja import Schema


class BookingOut(Schema):
    id: int
    class_id: int
    member_id: int
    status: str
    created_at: datetime
    cancelled_at: datetime | None = None


class WaitlistOut(Schema):
    id: int
    class_id: int
    member_id: int
    status: str
    joined_at: datetime