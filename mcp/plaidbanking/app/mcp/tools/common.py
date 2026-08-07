from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from plaidbanking.app.models.common import ApiResponse
from plaidbanking.app.plaid.exceptions import BankingError

T = TypeVar("T")


def serialize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, tuple):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    return value


async def tool_response(customer_id: str, source: str, operation: Callable[[], Awaitable[T]]) -> dict[str, Any]:
    try:
        result = await operation()
        return ApiResponse.ok(serialize(result), customer_id, source=source).model_dump(mode="json", exclude_none=True)
    except BankingError as exc:
        return ApiResponse.fail(exc.code, exc.safe_message, customer_id=customer_id, retryable=exc.retryable, source=source).model_dump(
            mode="json", exclude_none=True
        )
    except ValueError as exc:
        return ApiResponse.fail("INVALID_INPUT", str(exc), customer_id=customer_id, source=source).model_dump(mode="json", exclude_none=True)
    except Exception:
        return ApiResponse.fail(
            "INTERNAL_ERROR", "The banking request could not be completed safely.", customer_id=customer_id, retryable=True, source=source
        ).model_dump(mode="json", exclude_none=True)
