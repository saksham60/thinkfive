"""Correlation context for distributed tracing."""

from __future__ import annotations

import contextvars
import uuid

# Context variable for correlation ID
_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id",
    default="",
)


class CorrelationContext:
    """Context manager for correlation ID."""

    def __init__(self, correlation_id: str | None = None) -> None:
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.token: contextvars.Token[str] | None = None

    def __enter__(self) -> str:
        self.token = _correlation_id.set(self.correlation_id)
        return self.correlation_id

    def __exit__(self, *args: object) -> None:
        if self.token is not None:
            _correlation_id.reset(self.token)


def get_correlation_id() -> str:
    """Get current correlation ID or generate a new one."""
    correlation_id = _correlation_id.get()
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        _correlation_id.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    _correlation_id.set(correlation_id)
