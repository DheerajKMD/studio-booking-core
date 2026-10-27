from django.contrib.auth import authenticate

from apps.common.exceptions import DomainError

from .models import AuthToken, User


class InvalidCredentials(DomainError):
    status_code = 401
    code = "invalid_credentials"


def login(username: str, password: str) -> AuthToken:
    user = authenticate(username=username, password=password)
    if user is None or not isinstance(user, User):
        raise InvalidCredentials("Wrong username or password.")
    return AuthToken.objects.create(user=user)
