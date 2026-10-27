from django.http import HttpRequest
from ninja import Router

from . import services
from .schemas import LoginIn, LoginOut

router = Router(tags=["auth"])


@router.post("/login", response=LoginOut)
def login(request: HttpRequest, payload: LoginIn) -> LoginOut:
    token = services.login(payload.username, payload.password)
    return LoginOut(token=token.key, role=token.user.role)