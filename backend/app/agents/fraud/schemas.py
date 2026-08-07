"""Fraud Agent structured output schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class FraudEvidence(BaseModel):
    """Fraud evidence structure."""

    evidence_type: Literal["risk_assessment", "alert", "anomaly", "device_check", "blacklist_check"]
    data: dict | list
    source: str = "Fraud MCP"
    confidence: Literal["high", "medium", "low"] = "high"


class FraudAgentOutput(BaseModel):
    """Fraud Agent structured output."""

    goal_completed: bool
    evidence: list[FraudEvidence] = Field(default_factory=list)
    findings: str
    assessment_id: str | None = Field(default=None, description="Real assessment_id from Fraud MCP, never fabricated")
    alert_id: str | None = Field(default=None, description="Real alert_id from Fraud MCP, never fabricated")
    risk_score: float | None = Field(default=None, description="Actual risk score returned by Fraud MCP")
    severity: str | None = None
    requires_case: bool = Field(
        default=False, description="True if this risk level warrants case creation"
    )
    warnings: list[str] = Field(default_factory=list)
