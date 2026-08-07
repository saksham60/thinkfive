from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def now() -> datetime:
    return datetime.now(UTC)


def uid() -> str:
    return str(uuid4())


class Model(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, use_enum_values=True)


class CaseStatus(StrEnum):
    OPEN = "OPEN"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    ACTION_APPROVED = "ACTION_APPROVED"
    ACTION_REJECTED = "ACTION_REJECTED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CaseType(StrEnum):
    CUSTOMER_QUERY = "CUSTOMER_QUERY"
    TRANSACTION_DISPUTE = "TRANSACTION_DISPUTE"
    FRAUD_INVESTIGATION = "FRAUD_INVESTIGATION"
    ACCOUNT_ISSUE = "ACCOUNT_ISSUE"
    CARD_ISSUE = "CARD_ISSUE"
    OTHER = "OTHER"


class Priority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ActionType(StrEnum):
    FREEZE_CARD = "FREEZE_CARD"
    UNFREEZE_CARD = "UNFREEZE_CARD"
    BLOCK_CARD = "BLOCK_CARD"


class CardStatus(StrEnum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    BLOCKED = "BLOCKED"


class Case(Model):
    case_id: str = Field(default_factory=uid)
    customer_id: str
    case_type: CaseType
    title: str | None = None
    description: str | None = None
    status: CaseStatus = CaseStatus.OPEN
    priority: Priority = Priority.MEDIUM
    assigned_to: str | None = None
    fraud_alert_id: str | None = None
    assessment_id: str | None = None
    transaction_id: str | None = None
    account_id: str | None = None
    resolution: str | None = None
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class CaseNote(Model):
    note_id: str = Field(default_factory=uid)
    case_id: str
    author_type: str = "AGENT"
    author_id: str | None = None
    note_type: str = "GENERAL"
    content: str
    created_at: datetime = Field(default_factory=now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Approval(Model):
    approval_id: str = Field(default_factory=uid)
    case_id: str
    action_type: ActionType
    action_payload: dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str = "agent"
    requested_at: datetime = Field(default_factory=now)
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    expires_at: datetime | None = None
    idempotency_key: str | None = None
    executed_at: datetime | None = None


class CardState(Model):
    card_id: str
    customer_id: str
    account_id: str | None = None
    status: CardStatus = CardStatus.ACTIVE
    previous_status: CardStatus | None = None
    updated_at: datetime = Field(default_factory=now)
    updated_by: str = "SYSTEM"
    last_case_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=lambda: {"synthetic": True, "source": "demo_bank_control"})


class Notification(Model):
    notification_id: str = Field(default_factory=uid)
    case_id: str
    customer_id: str
    channel: str
    destination_masked: str | None = None
    subject: str | None = None
    content: str
    status: str = "QUEUED"
    provider: str = "SUPABASE_OUTBOX"
    created_at: datetime = Field(default_factory=now)
    sent_at: datetime | None = None
    failure_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class AuditEvent(Model):
    audit_id: str = Field(default_factory=uid)
    case_id: str | None = None
    customer_id: str | None = None
    actor_type: str = "SYSTEM"
    actor_id: str | None = None
    event_type: str
    entity_type: str
    entity_id: str
    action: str
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now)


ALLOWED_CASE_TRANSITIONS: dict[str, set[str]] = {
    "OPEN": {"TRIAGED", "INVESTIGATING", "AWAITING_APPROVAL", "RESOLVED"},
    "TRIAGED": {"INVESTIGATING", "AWAITING_APPROVAL", "RESOLVED"},
    "INVESTIGATING": {"AWAITING_APPROVAL", "RESOLVED"},
    "AWAITING_APPROVAL": {"ACTION_APPROVED", "ACTION_REJECTED", "INVESTIGATING"},
    "ACTION_APPROVED": {"INVESTIGATING", "RESOLVED"},
    "ACTION_REJECTED": {"INVESTIGATING", "RESOLVED"},
    "RESOLVED": {"CLOSED"},
    "CLOSED": set(),
}


CARD_TRANSITIONS = {"ACTIVE": {"FROZEN", "BLOCKED"}, "FROZEN": {"ACTIVE", "BLOCKED"}, "BLOCKED": set()}
