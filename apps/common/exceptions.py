class DomainError(Exception):
    """Base class for all business-rule errors."""

    status_code = 400
    code = "domain_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)
        self.message = message or self.code


class IdempotencyKeyReused(DomainError):
    status_code = 409
    code = "idempotency_key_reused"