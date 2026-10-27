from ninja import Schema


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
