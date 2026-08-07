from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from fraudMCP.app.errors import FraudError
from fraudMCP.app.logging import log_event
from fraudMCP.app.models.common import ApiResponse

T = TypeVar("T")

_LOGGER = logging.getLogger(__name__)


def serialize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, tuple):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    return value


async def tool_response(
    *,
    customer_id: str | None,
    source: str,
    tool_name: str,
    operation: Callable[[str], Awaitable[T]],
) -> dict[str, Any]:
    request_id = str(uuid4())
    started = time.perf_counter()
    try:
        result = await operation(request_id)
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            _LOGGER,
            logging.INFO,
            "fraud_tool_success",
            request_id=request_id,
            tool=tool_name,
            customer_id=customer_id,
            duration_ms=duration_ms,
            success=True,
        )
        return ApiResponse.ok(serialize(result), customer_id, source=source, request_id=request_id).model_dump(mode="json", exclude_none=True)
    except FraudError as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            _LOGGER,
            logging.WARNING,
            "fraud_tool_error",
            request_id=request_id,
            tool=tool_name,
            customer_id=customer_id,
            duration_ms=duration_ms,
            success=False,
            error_code=exc.code,
            retryable=exc.retryable,
        )
        return ApiResponse.fail(
            exc.code,
            exc.safe_message,
            customer_id=customer_id,
            source=source,
            request_id=request_id,
            retryable=exc.retryable,
        ).model_dump(mode="json", exclude_none=True)
    except ValueError as exc:
        return ApiResponse.fail(
            "INVALID_INPUT",
            str(exc),
            customer_id=customer_id,
            source=source,
            request_id=request_id,
            retryable=False,
        ).model_dump(mode="json", exclude_none=True)
    except Exception:
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            _LOGGER,
            logging.ERROR,
            "fraud_tool_unhandled",
            request_id=request_id,
            tool=tool_name,
            customer_id=customer_id,
            duration_ms=duration_ms,
            success=False,
        )
        return ApiResponse.fail(
            "INTERNAL_ERROR",
            "The fraud request could not be completed safely.",
            customer_id=customer_id,
            source=source,
            request_id=request_id,
            retryable=True,
        ).model_dump(mode="json", exclude_none=True)
