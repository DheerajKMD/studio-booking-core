from datetime import datetime

from ninja import Schema
from pydantic import Field


class StudioIn(Schema):
    name: str = Field(min_length=1, max_length=200)
    timezone: str
    cancellation_cutoff_hours: int = Field(default=4, ge=0)


class StudioUpdateIn(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    timezone: str | None = None
    cancellation_cutoff_hours: int | None = Field(default=None, ge=0)


class StudioOut(Schema):
    id: int
    name: str
    timezone: str
    cancellation_cutoff_hours: int


class ClassIn(Schema):
    title: str = Field(min_length=1, max_length=200)
    starts_at: datetime
    duration_minutes: int = Field(gt=0)
    capacity: int = Field(gt=0)
    credit_cost: int = Field(gt=0)


class ClassOut(Schema):
    id: int
    studio_id: int
    title: str
    starts_at: datetime
    duration_minutes: int
    capacity: int
    credit_cost: int
    spots_available: int