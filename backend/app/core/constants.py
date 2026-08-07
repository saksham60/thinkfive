"""Application constants."""

from enum import Enum

# Canonical customer identifier
CANONICAL_CUSTOMER_ID = "demo_customer_001"
CUSTOMER_DISPLAY_ID = "CUST-1001"


class Role(str, Enum):
    """User roles for RBAC."""

    CUSTOMER = "CUSTOMER"
    ANALYST = "ANALYST"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class RunStatus(str, Enum):
    """Agent run execution status."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"


class InterruptStatus(str, Enum):
    """Workflow interrupt status."""

    WAITING = "WAITING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESUMED = "RESUMED"
    CANCELLED = "CANCELLED"


class MemoryStatus(str, Enum):
    """Customer memory status."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class MemoryType(str, Enum):
    """Customer memory types."""

    PREFERENCE = "PREFERENCE"
    COMMUNICATION_PREFERENCE = "COMMUNICATION_PREFERENCE"
    SUMMARY = "SUMMARY"
    CONTEXT_REFERENCE = "CONTEXT_REFERENCE"


class EventType(str, Enum):
    """SSE event types."""

    # Connection
    CONNECTION_READY = "connection.ready"
    HEARTBEAT = "heartbeat"

    # Chat
    CHAT_ACCEPTED = "chat.accepted"
    CHAT_COMPLETED = "chat.completed"
    CHAT_FAILED = "chat.failed"

    # Agent
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    # Tool
    AGENT_TOOL_STARTED = "agent.tool.started"
    AGENT_TOOL_COMPLETED = "agent.tool.completed"
    AGENT_TOOL_FAILED = "agent.tool.failed"

    # Assistant
    ASSISTANT_DELTA = "assistant.delta"
    ASSISTANT_MESSAGE = "assistant.message"

    # Transaction
    TRANSACTION_DETECTED = "transaction.detected"
    TRANSACTION_ASSESSED = "transaction.assessed"

    # Fraud
    FRAUD_ASSESSMENT_CREATED = "fraud.assessment.created"
    FRAUD_ALERT_CREATED = "fraud.alert.created"
    FRAUD_ALERT_UPDATED = "fraud.alert.updated"

    # Case
    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"
    CASE_NOTE_ADDED = "case.note.added"

    # Approval
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"

    # Workflow
    WORKFLOW_INTERRUPTED = "workflow.interrupted"
    WORKFLOW_RESUMED = "workflow.resumed"

    # Card
    CARD_STATE_UPDATED = "card.state.updated"

    # Notification
    NOTIFICATION_CREATED = "notification.created"

    # System
    SYSTEM_WARNING = "system.warning"
