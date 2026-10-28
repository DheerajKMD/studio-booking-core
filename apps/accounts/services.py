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


class UsernameTaken(DomainError):
    status_code = 409
    code = "username_taken"


def create_user(username: str, password: str, role: str) -> User:
    if User.objects.filter(username=username).exists():
        raise UsernameTaken(f"Username '{username}' is already taken.")
    user: User = User.objects.create_user(username, password=password, role=role)
    return user
