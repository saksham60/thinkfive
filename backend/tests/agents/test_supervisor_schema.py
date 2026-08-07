"""Supervisor routing schema test - ensures structured output, no keyword routing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents.supervisor.schemas import SupervisorDecision


class TestSupervisorDecisionSchema:
    def test_valid_decision(self) -> None:
        decision = SupervisorDecision(
            next_agent="banking",
            goal="retrieve account balance",
            reason="customer asked for balance",
        )
        assert decision.next_agent == "banking"
        assert decision.needs_clarification is False

    def test_invalid_agent_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SupervisorDecision(next_agent="not_a_real_agent", goal="x", reason="y")  # type: ignore[arg-type]

    def test_clarification_fields_optional(self) -> None:
        decision = SupervisorDecision(
            next_agent="synthesis",
            goal="ask which transaction",
            reason="ambiguous request",
            needs_clarification=True,
            clarification_question="Which transaction do you mean?",
        )
        assert decision.needs_clarification is True
        assert decision.clarification_question is not None
