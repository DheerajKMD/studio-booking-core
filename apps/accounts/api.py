from django.http import HttpRequest
from ninja import Router

from . import services
from .auth import TokenAuth
from .models import User
from .permissions import ensure_self_or_staff, require_staff
from .schemas import LoginIn, LoginOut, MeOut

router = Router(tags=["auth"])


@router.post("/login", response=LoginOut)
def login(request: HttpRequest, payload: LoginIn) -> LoginOut:
    token = services.login(payload.username, payload.password)
    return LoginOut(token=token.key, role=token.user.role)


@router.get("/me", response=MeOut, auth=TokenAuth())
def me(request: HttpRequest) -> MeOut:
    user: User = request.auth  # type: ignore[attr-defined]
    return MeOut(id=user.pk, username=user.username, role=user.role)


@router.get("/staff-only", auth=TokenAuth())
def staff_only(request: HttpRequest) -> dict[str, str]:
    require_staff(request.auth)  # type: ignore[attr-defined]
    return {"detail": "hello staff"}


@router.get("/members/{member_id}/check", auth=TokenAuth())
def member_check(request: HttpRequest, member_id: int) -> dict[str, str]:
    ensure_self_or_staff(request.auth, member_id)  # type: ignore[attr-defined]
    return {"detail": "allowed"}