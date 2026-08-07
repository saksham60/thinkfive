"""Unit tests for PII detection and secret redaction."""

from __future__ import annotations

from app.security.pii import PIIDetector
from app.security.redaction import redact_secrets


class TestPIIDetector:
    def test_detects_card_number(self) -> None:
        detector = PIIDetector()
        assert "card_number" in detector.detect("my card is 4111111111111111")

    def test_detects_cvv(self) -> None:
        detector = PIIDetector()
        assert "cvv" in detector.detect("cvv: 123")

    def test_detects_otp(self) -> None:
        detector = PIIDetector()
        assert "otp" in detector.detect("otp = 123456")

    def test_clean_text_has_no_pii(self) -> None:
        detector = PIIDetector()
        assert detector.contains_pii("What is my account balance?") is False


class TestRedaction:
    def test_redacts_password(self) -> None:
        result = redact_secrets("my password: hunter2")
        assert "hunter2" not in result
        assert "[REDACTED_PASSWORD]" in result

    def test_redacts_api_token(self) -> None:
        result = redact_secrets("Authorization: Bearer sk-abc123def456ghi789")
        assert "sk-abc123def456ghi789" not in result
