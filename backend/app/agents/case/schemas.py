"""Case Agent structured output schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class CaseEvidence(BaseModel):
    """Case evidence structure."""

    evidence_type: Literal["case", "note", "approval_request", "notification"]
    data: dict
    source: str = "Case MCP"


class CaseAgentOutput(BaseModel):
    """Case Agent structured output."""

    goal_completed: bool
    evidence: list[CaseEvidence] = Field(default_factory=list)
    findings: str
    case_id: str | None = Field(default=None, description="Real case_id from Case MCP, never fabricated")
    approval_id: str | None = Field(
        default=None, description="Real approval_id from request_approval, never fabricated"
    )
    approval_requested: bool = Field(
        default=False, description="True if a human approval request was created this turn"
    )
    warnings: list[str] = Field(default_factory=list)
