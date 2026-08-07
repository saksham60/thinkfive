"""Memory extraction - identifies candidate memories from conversation turns.

Only extracts from an explicit, narrow allowlist of categories. Does NOT let
the LLM freely decide what to remember; extraction targets specific patterns
and always passes through MemoryPolicyEnforcer before storage.
"""

from __future__ import annotations

import re

from app.memory.models import MemoryCandidate

_LANGUAGE_PATTERN = re.compile(
    r"\b(prefer|speak|respond)\b.*\b(in|to)\b\s+(english|spanish|french|hindi|german)",
    re.IGNORECASE,
)

_COMMUNICATION_PATTERN = re.compile(
    r"\b(prefer|contact me|notify me)\b.*\b(email|sms|text|phone|call)\b",
    re.IGNORECASE,
)


class MemoryExtractor:
    """Extracts narrow, allowed memory candidates from a user message."""

    def extract(self, user_message: str) -> list[MemoryCandidate]:
        candidates: list[MemoryCandidate] = []

        lang_match = _LANGUAGE_PATTERN.search(user_message)
        if lang_match:
            language = lang_match.group(3).lower()
            candidates.append(
                MemoryCandidate(
                    memory_type="PREFERENCE",
                    memory_key="preferred_language",
                    content=language,
                    confidence=0.8,
                )
            )

        comm_match = _COMMUNICATION_PATTERN.search(user_message)
        if comm_match:
            channel = comm_match.group(2).lower()
            candidates.append(
                MemoryCandidate(
                    memory_type="COMMUNICATION_PREFERENCE",
                    memory_key="preferred_channel",
                    content=channel,
                    confidence=0.7,
                )
            )

        return candidates
