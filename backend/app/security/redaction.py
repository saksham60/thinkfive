"""Secret/PII redaction for logging and memory storage."""

from __future__ import annotations

import re

_REDACTION_PATTERNS = [
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[REDACTED_CARD_NUMBER]"),
    (re.compile(r"\bcvv\s*[:=]?\s*\d{3,4}\b", re.IGNORECASE), "[REDACTED_CVV]"),
    (re.compile(r"\bpin\s*[:=]?\s*\d{4,6}\b", re.IGNORECASE), "[REDACTED_PIN]"),
    (re.compile(r"\botp\s*[:=]?\s*\d{4,8}\b", re.IGNORECASE), "[REDACTED_OTP]"),
    (re.compile(r"\bpassword\s*[:=]?\s*\S+", re.IGNORECASE), "[REDACTED_PASSWORD]"),
    (re.compile(r"\b(sk-|Bearer\s+)[A-Za-z0-9_\-\.]{10,}"), "[REDACTED_TOKEN]"),
]


def redact_secrets(text: str) -> str:
    """Redact known secret/PII patterns from a string before logging or storage."""
    result = text
    for pattern, replacement in _REDACTION_PATTERNS:
        result = pattern.sub(replacement, result)
    return result
