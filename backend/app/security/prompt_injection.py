"""Prompt injection detection heuristics for Knowledge Agent RAG defense."""

from __future__ import annotations

import re

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+|previous\s+|above\s+)*instructions", re.IGNORECASE),
    re.compile(r"you are now\s+(a|an)\s+\w+", re.IGNORECASE),
    re.compile(r"disregard (all |the )?(system|previous) prompt", re.IGNORECASE),
    re.compile(r"reveal (your|the) system prompt", re.IGNORECASE),
    re.compile(r"act as\s+(if|an?)\b", re.IGNORECASE),
    re.compile(r"new instructions?:", re.IGNORECASE),
]


class PromptInjectionDetector:
    """Detects likely prompt-injection attempts in retrieved/untrusted content."""

    def detect(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)

    def scan_chunks(self, chunks: list[str]) -> list[int]:
        """Return indices of chunks that appear to contain injection attempts."""
        return [i for i, c in enumerate(chunks) if self.detect(c)]
