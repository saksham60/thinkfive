"""Synthesis Agent structured output schemas."""

from pydantic import BaseModel, Field


class SynthesisOutput(BaseModel):
    """Synthesis Agent structured output - the final customer-facing message."""

    final_response: str = Field(description="Final grounded customer-facing message")
    workflow_status: str = Field(
        description="One of: RESOLVED, AWAITING_APPROVAL, NEEDS_CLARIFICATION, PARTIAL_EVIDENCE"
    )
    grounded_claims: list[str] = Field(
        default_factory=list, description="List of claims made, each traceable to evidence"
    )
    warnings: list[str] = Field(default_factory=list)
