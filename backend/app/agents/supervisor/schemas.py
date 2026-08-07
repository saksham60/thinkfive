"""Supervisor Agent structured output schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class SupervisorDecision(BaseModel):
    """Structured routing decision - NO keyword routing, model reasons over state."""

    next_agent: Literal["banking", "fraud", "knowledge", "case", "synthesis"] = Field(
        description="Which specialist agent to route to next"
    )
    goal: str = Field(description="Specific objective for the next agent to accomplish")
    reason: str = Field(description="Why this agent/goal was chosen given current evidence")
    evidence_required: list[str] = Field(
        default_factory=list,
        description="Evidence types still needed (e.g., account_summary, risk_assessment)",
    )
    needs_clarification: bool = Field(
        default=False,
        description="True if the customer's request is ambiguous and needs a follow-up question",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask the customer if needs_clarification is true",
    )
