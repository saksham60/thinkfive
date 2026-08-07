"""Evaluation scorers - deterministic checks per category (no fake 100% scores)."""

from __future__ import annotations

from typing import Any


class RoutingScorer:
    """Checks that supervisor routed to the expected agent."""

    def score(self, expected_agent: str | None, actual_agent: str | None) -> bool:
        if expected_agent is None:
            return True
        return expected_agent == actual_agent


class GroundingScorer:
    """Checks that claims reference real evidence identifiers (no fabrication)."""

    def score(self, output: dict[str, Any], required_evidence_keys: list[str]) -> bool:
        for key in required_evidence_keys:
            if not output.get(key):
                return False
        return True


class PIIScorer:
    """Checks that no PII/secret patterns leaked into the final response."""

    def score(self, response_text: str) -> bool:
        from app.security.pii import PIIDetector

        return not PIIDetector().contains_pii(response_text)
