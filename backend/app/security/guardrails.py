"""Guardrails - pre-LLM-invocation safety checks (composition of PII/injection detectors)."""

from __future__ import annotations

import logging

from app.security.pii import PIIDetector
from app.security.prompt_injection import PromptInjectionDetector
from app.security.redaction import redact_secrets

logger = logging.getLogger(__name__)


class Guardrails:
    """Applies safety checks before LLM invocation and before persistence."""

    def __init__(self) -> None:
        self.pii_detector = PIIDetector()
        self.injection_detector = PromptInjectionDetector()

    def sanitize_for_logging(self, text: str) -> str:
        """Redact secrets before any log line or persisted trace."""
        return redact_secrets(text)

    def check_user_input(self, text: str) -> list[str]:
        """Return warnings if user input contains PII that should not be echoed/stored."""
        warnings = []
        found = self.pii_detector.detect(text)
        if found:
            warnings.append(f"User input contains sensitive patterns: {', '.join(found)}")
        return warnings

    def check_retrieved_content(self, chunks: list[str]) -> list[str]:
        """Flag retrieved RAG chunks that appear to contain prompt injection."""
        flagged = self.injection_detector.scan_chunks(chunks)
        if flagged:
            return [f"Potential prompt injection detected in retrieved chunk index {i}" for i in flagged]
        return []
