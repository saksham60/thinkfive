from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


T = TypeVar("T")


class ApiResponse(StrictModel, Generic[T]):
    success: bool
    source: str = "fraud_engine"
    customer_id: str | None = None
    request_id: str | None = None
    retrieved_at: datetime = Field(default_factory=utc_now)
    data: T | None = None
    warnings: tuple[str, ...] = ()
    error_code: str | None = None
    message: str | None = None
    retryable: bool | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> ApiResponse[T]:
        if self.success and self.error_code is not None:
            raise ValueError("success responses must not include error_code")
        if not self.success and self.error_code is None:
            raise ValueError("failure responses must include error_code")
        return self

    @classmethod
    def ok(
        cls,
        data: T,
        customer_id: str | None = None,
        *,
        source: str = "fraud_engine",
        request_id: str | None = None,
        warnings: tuple[str, ...] = (),
    ) -> "ApiResponse[T]":
        return cls(success=True, source=source, customer_id=customer_id, request_id=request_id, data=data, warnings=warnings)

    @classmethod
    def fail(
        cls,
        error_code: str,
        message: str,
        *,
        customer_id: str | None = None,
        source: str = "fraud_engine",
        request_id: str | None = None,
        retryable: bool = False,
    ) -> "ApiResponse[Any]":
        return cls(
            success=False,
            source=source,
            customer_id=customer_id,
            request_id=request_id,
            error_code=error_code,
            message=message,
            retryable=retryable,
        )
