from datetime import datetime

from django.core.exceptions import ValidationError

from apps.common.exceptions import DomainError

from .models import ClassSession, Studio
from .validators import validate_iana_timezone


class InvalidTimezone(DomainError):
    status_code = 422
    code = "invalid_timezone"


class StudioNotFound(DomainError):
    status_code = 404
    code = "studio_not_found"


def create_studio(name: str, timezone: str, cancellation_cutoff_hours: int) -> Studio:
    _check_timezone(timezone)
    return Studio.objects.create(
        name=name,
        timezone=timezone,
        cancellation_cutoff_hours=cancellation_cutoff_hours,
    )


def update_studio(
    studio_id: int,
    name: str | None = None,
    timezone: str | None = None,
    cancellation_cutoff_hours: int | None = None,
) -> Studio:
    studio = get_studio(studio_id)
    if name is not None:
        studio.name = name
    if timezone is not None:
        _check_timezone(timezone)
        studio.timezone = timezone
    if cancellation_cutoff_hours is not None:
        studio.cancellation_cutoff_hours = cancellation_cutoff_hours
    studio.save()
    return studio


def get_studio(studio_id: int) -> Studio:
    try:
        return Studio.objects.get(pk=studio_id)
    except Studio.DoesNotExist:
        raise StudioNotFound(f"Studio {studio_id} not found.") from None


def schedule_class(
    studio_id: int,
    title: str,
    starts_at: datetime,
    duration_minutes: int,
    capacity: int,
    credit_cost: int,
) -> ClassSession:
    studio = get_studio(studio_id)
    return ClassSession.objects.create(
        studio=studio,
        title=title,
        starts_at=starts_at,
        duration_minutes=duration_minutes,
        capacity=capacity,
        credit_cost=credit_cost,
    )


def _check_timezone(value: str) -> None:
    try:
        validate_iana_timezone(value)
    except ValidationError as exc:
        raise InvalidTimezone(exc.messages[0]) from None
