"""Core configuration and utilities."""

from .config import Settings, get_settings
from .constants import (
    CANONICAL_CUSTOMER_ID,
    CUSTOMER_DISPLAY_ID,
    Role,
    RunStatus,
)
from .correlation import CorrelationContext, get_correlation_id
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    DomainError,
    MCPError,
    NotFoundError,
    ValidationError,
)

__all__ = [
    "Settings",
    "get_settings",
    "CANONICAL_CUSTOMER_ID",
    "CUSTOMER_DISPLAY_ID",
    "Role",
    "RunStatus",
    "CorrelationContext",
    "get_correlation_id",
    "DomainError",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "MCPError",
]
