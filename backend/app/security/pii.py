"""PII detection patterns."""

from __future__ import annotations

import re

_PATTERNS = {
    "card_number": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "cvv": re.compile(r"\bcvv\s*[:=]?\s*\d{3,4}\b", re.IGNORECASE),
    "pin": re.compile(r"\bpin\s*[:=]?\s*\d{4,6}\b", re.IGNORECASE),
    "otp": re.compile(r"\botp\s*[:=]?\s*\d{4,8}\b", re.IGNORECASE),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


class PIIDetector:
    """Detects presence of common PII/secret patterns in text."""

    def detect(self, text: str) -> list[str]:
        found = []
        for name, pattern in _PATTERNS.items():
            if pattern.search(text):
                found.append(name)
        return found

    def contains_pii(self, text: str) -> bool:
        return len(self.detect(text)) > 0
