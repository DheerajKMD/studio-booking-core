import hashlib
import json
from collections.abc import Callable
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.db import IntegrityError, transaction

from .exceptions import IdempotencyKeyReused
from .models import IdempotencyRecord


def hash_request(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def run_idempotent(
    member: AbstractBaseUser,
    key: str | None,
    payload: dict[str, Any],
    action: Callable[[], tuple[int, dict[str, Any]]],
) -> tuple[int, dict[str, Any]]:
    """Run `action` at most once per (member, key).

    `action` returns (status_code, json_body). A retry gets the stored result.
    Without a key the action simply runs.
    """
    if not key:
        return action()

    request_hash = hash_request(payload)
    with transaction.atomic():
        try:
            with transaction.atomic():
                record = IdempotencyRecord.objects.create(
                    key=key, member=member, request_hash=request_hash
                )
        except IntegrityError:
            record = IdempotencyRecord.objects.select_for_update().get(
                key=key, member=member
            )
            if record.request_hash != request_hash:
                raise IdempotencyKeyReused(
                    "This Idempotency-Key was used with a different request."
                ) from None
            if record.response_status is not None:
                return record.response_status, record.response_body or {}
            raise IdempotencyKeyReused(
                "A request with this key is in progress."
            ) from None

        status, body = action()
        record.response_status = status
        record.response_body = body
        record.save(update_fields=["response_status", "response_body"])
        return status, body
