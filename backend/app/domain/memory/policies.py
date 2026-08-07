"""Memory domain policies."""

from dataclasses import dataclass


@dataclass
class MemoryPolicy:
    """Policy for customer memory storage and retrieval."""

    # Forbidden memory types
    FORBIDDEN_KEYS = frozenset(
        [
            "otp",
            "pin",
            "cvv",
            "password",
            "secret",
            "access_token",
            "refresh_token",
            "api_key",
            "card_number",
            "ssn",
            "tax_id",
        ]
    )

    # Allowed memory types
    ALLOWED_TYPES = frozenset(
        [
            "PREFERENCE",
            "COMMUNICATION_PREFERENCE",
            "SUMMARY",
            "CONTEXT_REFERENCE",
        ]
    )

    @staticmethod
    def can_store(memory_type: str, memory_key: str | None, content: str | None) -> bool:
        """Check if memory can be stored."""
        # Type must be allowed
        if memory_type not in MemoryPolicy.ALLOWED_TYPES:
            return False

        # Check for forbidden keys in memory key
        if memory_key:
            key_lower = memory_key.lower()
            if any(forbidden in key_lower for forbidden in MemoryPolicy.FORBIDDEN_KEYS):
                return False

        # Check for forbidden content patterns
        if content:
            content_lower = content.lower()
            if any(forbidden in content_lower for forbidden in MemoryPolicy.FORBIDDEN_KEYS):
                return False

        return True

    @staticmethod
    def should_expire(created_at: object, ttl_days: int) -> bool:
        """Check if memory should expire based on TTL."""
        from datetime import datetime, timedelta

        if not isinstance(created_at, datetime):
            return False

        age = datetime.utcnow() - created_at
        return age > timedelta(days=ttl_days)
