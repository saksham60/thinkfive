"""Unit tests for MemoryPolicy - mandatory safety tests (section 64)."""

from __future__ import annotations

from app.domain.memory.policies import MemoryPolicy


class TestMemoryPolicy:
    def test_allowed_preference_can_be_stored(self) -> None:
        assert MemoryPolicy.can_store("PREFERENCE", "preferred_language", "english") is True

    def test_communication_preference_can_be_stored(self) -> None:
        assert MemoryPolicy.can_store("COMMUNICATION_PREFERENCE", "preferred_channel", "email") is True

    def test_otp_rejected(self) -> None:
        assert MemoryPolicy.can_store("PREFERENCE", "otp_code", "123456") is False

    def test_otp_in_content_rejected(self) -> None:
        assert MemoryPolicy.can_store("PREFERENCE", "note", "the otp was 123456") is False

    def test_pin_rejected(self) -> None:
        assert MemoryPolicy.can_store("PREFERENCE", "pin", "1234") is False

    def test_password_rejected(self) -> None:
        assert MemoryPolicy.can_store("PREFERENCE", "password_hint", "mypassword") is False

    def test_cvv_rejected(self) -> None:
        assert MemoryPolicy.can_store("PREFERENCE", "cvv_value", "123") is False

    def test_card_number_rejected(self) -> None:
        assert MemoryPolicy.can_store("PREFERENCE", "card_number", "4111111111111111") is False

    def test_disallowed_memory_type_rejected(self) -> None:
        assert MemoryPolicy.can_store("UNVERIFIED_FRAUD_FACT", "allegation", "customer says fraud") is False

    def test_unverified_fraud_allegation_not_a_valid_type(self) -> None:
        # Only the explicit allowlist of types may be persisted.
        for invalid_type in ("FRAUD_FACT", "RANDOM_LLM_FACT", ""):
            assert MemoryPolicy.can_store(invalid_type, "key", "content") is False

    def test_summary_type_allowed(self) -> None:
        assert MemoryPolicy.can_store("SUMMARY", None, "customer discussed a billing question") is True
