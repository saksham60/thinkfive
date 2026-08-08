"""Supervisor Agent structured output schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class SupervisorDecision(BaseModel):
    """Structured routing decision - NO keyword routing, model reasons over state."""

    next_agent: Literal["banking", "fraud", "knowledge", "case", "synthesis"] = Field(
        description="Which specialist agent to route to next"
    )
    goal: str = Field(description="Specific objective for the next agent to accomplish")
    primary_user_goal: str | None = Field(
        default=None,
        description="The customer's overall goal, preserved while prerequisites are gathered",
    )
    customer_requested_formal_case: bool = Field(
        default=False,
        description=(
            "True only when the customer explicitly asks to report, dispute, or formally "
            "investigate an unauthorized transaction; independent of model risk severity"
        ),
    )
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
    reference_type: Literal[
        "none", "active_transaction", "ordinal", "merchant_amount", "pending_confirmation"
    ] = Field(
        default="none",
        description="Semantic transaction reference used in the latest customer message",
    )
    candidate_position: int | None = Field(
        default=None,
        description="One-based position when the customer refers to an item in a displayed list",
    )
    reference_merchant: str | None = Field(
        default=None,
        description="Merchant or description stated by the customer for a targeted search",
    )
    reference_amount: float | None = Field(
        default=None,
        description="Amount stated by the customer for a targeted search",
    )
    reference_date: str | None = Field(
        default=None,
        description="Date stated by the customer for a targeted transaction search",
    )
    confirmation: Literal["none", "accept", "reject"] = Field(
        default="none",
        description="Whether the customer accepted or rejected a pending conversational selection",
    )
    clear_pending_confirmation: bool = Field(
        default=False,
        description="True when the customer clearly changes topic instead of answering a pending question",
    )
