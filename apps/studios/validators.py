from zoneinfo import available_timezones

from django.core.exceptions import ValidationError


def validate_iana_timezone(value: str) -> None:
    if value not in available_timezones():
        raise ValidationError(f"'{value}' is not a valid IANA timezone.")
