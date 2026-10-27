from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apps.studios.models import ClassSession


def cutoff_for(session: ClassSession) -> datetime:
    """Cancellation deadline, computed in the studio's local time."""
    tz = ZoneInfo(session.studio.timezone)
    local_start = session.starts_at.astimezone(tz)
    return local_start - timedelta(hours=session.studio.cancellation_cutoff_hours)


def is_refundable(session: ClassSession, now: datetime) -> bool:
    """True if `now` is at or before the cutoff."""
    return now <= cutoff_for(session)
