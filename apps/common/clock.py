from datetime import datetime
from typing import Protocol

from django.utils import timezone


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return timezone.now()


class FixedClock:
    """Used in tests to control time."""

    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed

    def set(self, fixed: datetime) -> None:
        self._fixed = fixed


default_clock: Clock = SystemClock()
