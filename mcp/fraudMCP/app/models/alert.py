from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from .assessment import RiskSeverity
from .common import StrictModel


class AlertStatus(StrEnum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class AlertPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class AlertStatusEvent(StrictModel):
    status: AlertStatus
    changed_at: datetime
    note: str | None = None


class FraudAlert(StrictModel):
    alert_id: str
    assessment_id: str
    customer_id: str
    transaction_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    severity: RiskSeverity
    priority: AlertPriority
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    notes: tuple[str, ...] = ()
    evidence: tuple[dict[str, object], ...] = ()
    history: tuple[AlertStatusEvent, ...] = ()
