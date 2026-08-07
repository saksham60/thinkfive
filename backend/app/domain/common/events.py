"""Common domain events."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    """Base domain event."""

    event_id: UUID
    timestamp: datetime
    correlation_id: str


@dataclass(frozen=True)
class AgentExecutionStarted(DomainEvent):
    """Agent execution started."""

    run_id: UUID
    agent_name: str


@dataclass(frozen=True)
class AgentExecutionCompleted(DomainEvent):
    """Agent execution completed."""

    run_id: UUID
    agent_name: str
    duration_ms: float


@dataclass(frozen=True)
class AgentExecutionFailed(DomainEvent):
    """Agent execution failed."""

    run_id: UUID
    agent_name: str
    error: str
