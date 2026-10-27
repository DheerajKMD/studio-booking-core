from apps.common.exceptions import DomainError

from .models import User


class PermissionDenied(DomainError):
    status_code = 403
    code = "permission_denied"


def require_staff(user: User) -> None:
    if not user.is_studio_staff:
        raise PermissionDenied("Staff access required.")


def ensure_self_or_staff(user: User, member_id: int) -> None:
    """Members may only act on their own data; staff may act on anyone's."""
    if user.is_studio_staff:
        return
    if user.pk != member_id:
        raise PermissionDenied("You can only access your own data.")