from typing import Literal

from ninja import Schema
from pydantic import Field


class LoginIn(Schema):
    username: str
    password: str


class LoginOut(Schema):
    token: str
    role: str


class MeOut(Schema):
    id: int
    username: str
    role: str


class UserCreateIn(Schema):
    username: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8)
    role: Literal["staff", "member"] = "member"
