from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from .common import StrictModel
from .feature import FeatureValue


class RiskSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AssessmentInputContext(StrictModel):
    device_id: str | None = None
    ip_address: str | None = None
    channel: str | None = None


class AssessmentThresholds(StrictModel):
    medium: float = Field(ge=0.0, le=1.0)
    high: float = Field(ge=0.0, le=1.0)
    critical: float = Field(ge=0.0, le=1.0)
    alert: float = Field(ge=0.0, le=1.0)


class TransactionSnapshot(StrictModel):
    transaction_id: str
    account_id: str
    amount: float
    currency: str | None = None
    merchant_name: str | None = None
    transaction_name: str | None = None
    date: str | None = None
    datetime: str | None = None
    category: tuple[str, ...] = ()
    location: dict[str, Any] | None = None


class RiskAssessment(StrictModel):
    assessment_id: str
    customer_id: str
    transaction_id: str
    created_at: datetime
    data_timestamp: datetime
    risk_score: float = Field(ge=0.0, le=1.0)
    severity: RiskSeverity
    feature_values: tuple[FeatureValue, ...]
    triggered_signals: tuple[str, ...]
    evidence: dict[str, Any]
    scorer_name: str
    scorer_version: str
    feature_schema_version: int = Field(ge=1)
    warnings: tuple[str, ...] = ()
    recommended_action: str | None = None
    input_context: AssessmentInputContext
    thresholds: AssessmentThresholds
    target_transaction_snapshot: TransactionSnapshot
