"""Memory extraction tests - mandatory section 64 subset that runs without a live DB."""

from __future__ import annotations

from app.memory.extractor import MemoryExtractor
from app.memory.policy import MemoryPolicyEnforcer


class TestMemoryExtractor:
    def test_extracts_language_preference(self) -> None:
        extractor = MemoryExtractor()
        candidates = extractor.extract("I prefer to speak in spanish please")
        assert any(c.memory_key == "preferred_language" for c in candidates)

    def test_extracts_communication_preference(self) -> None:
        extractor = MemoryExtractor()
        candidates = extractor.extract("Please contact me by email in the future")
        assert any(c.memory_key == "preferred_channel" for c in candidates)

    def test_no_candidates_for_unrelated_message(self) -> None:
        extractor = MemoryExtractor()
        candidates = extractor.extract("What is my account balance?")
        assert candidates == []


class TestMemoryPolicyEnforcer:
    def test_rejects_otp_candidate(self) -> None:
        from app.memory.models import MemoryCandidate

        enforcer = MemoryPolicyEnforcer()
        candidate = MemoryCandidate(memory_type="PREFERENCE", memory_key="otp", content="123456")
        assert enforcer.can_store(candidate) is False

    def test_allows_valid_preference_candidate(self) -> None:
        from app.memory.models import MemoryCandidate

        enforcer = MemoryPolicyEnforcer()
        candidate = MemoryCandidate(
            memory_type="PREFERENCE", memory_key="preferred_language", content="english"
        )
        assert enforcer.can_store(candidate) is True
