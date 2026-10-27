from apps.common.exceptions import DomainError


class InsufficientCredits(DomainError):
    status_code = 402
    code = "insufficient_credits"


class InvalidPack(DomainError):
    status_code = 422
    code = "invalid_pack"
