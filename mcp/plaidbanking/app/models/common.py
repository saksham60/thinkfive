from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


T = TypeVar("T")


class ErrorDetail(StrictModel):
    error_code: str
    message: str
    retryable: bool = False


class ApiResponse(StrictModel, Generic[T]):
    success: bool
    source: str = "plaid_sandbox"
    customer_id: str | None = None
    retrieved_at: datetime = Field(default_factory=utc_now)
    data: T | None = None
    warnings: tuple[str, ...] = ()
    error: ErrorDetail | None = None

    @classmethod
    def ok(cls, data: T, customer_id: str | None = None, *, source: str = "plaid_sandbox", warnings: tuple[str, ...] = ()) -> ApiResponse[T]:
        return cls(success=True, source=source, customer_id=customer_id, data=data, warnings=warnings)

    @classmethod
    def fail(cls, code: str, message: str, *, customer_id: str | None = None, retryable: bool = False, source: str = "plaid_sandbox") -> ApiResponse[Any]:
        return cls(success=False, source=source, customer_id=customer_id, error=ErrorDetail(error_code=code, message=message, retryable=retryable))
