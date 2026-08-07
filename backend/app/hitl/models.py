"""HITL subsystem models."""

from pydantic import BaseModel


class ApprovalDecisionPayload(BaseModel):
    """Trusted resume payload constructed from verified Case MCP state (not client input)."""

    approval_id: str
    decision: str  # APPROVED | REJECTED
    action_result: dict | None = None
