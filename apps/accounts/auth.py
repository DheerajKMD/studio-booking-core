from django.http import HttpRequest
from ninja.security import HttpBearer

from .models import AuthToken, User


class TokenAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> User | None:
        auth_token = (
            AuthToken.objects.select_related("user")
            .filter(key=token, user__is_active=True)
            .first()
        )
        return auth_token.user if auth_token else None


def get_user(request: HttpRequest) -> User:
    user = getattr(request, "auth", None)
    assert isinstance(user, User)
    return user
