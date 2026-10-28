from django.http import HttpRequest
from ninja import Router

from . import services
from .auth import TokenAuth, get_user
from .permissions import require_staff
from .schemas import LoginIn, LoginOut, MeOut, UserCreateIn

router = Router(tags=["auth"])


@router.post("/login", response=LoginOut)
def login(request: HttpRequest, payload: LoginIn) -> LoginOut:
    token = services.login(payload.username, payload.password)
    return LoginOut(token=token.key, role=token.user.role)


@router.get("/me", response=MeOut, auth=TokenAuth())
def me(request: HttpRequest) -> MeOut:
    user = get_user(request)
    return MeOut(id=user.pk, username=user.username, role=user.role)


@router.post("/users", response={201: MeOut}, auth=TokenAuth())
def create_user(request: HttpRequest, payload: UserCreateIn) -> tuple[int, MeOut]:
    require_staff(get_user(request))
    user = services.create_user(payload.username, payload.password, payload.role)
    return 201, MeOut(id=user.pk, username=user.username, role=user.role)
