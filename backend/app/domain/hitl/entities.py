"""HITL domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass
class WorkflowInterrupt:
    """Workflow interrupt for HITL."""

    interrupt_id: UUID
    run_id: UUID
    conversation_id: UUID
    thread_id: str
    customer_id: str | None
    case_id: str | None
    approval_id: str | None
    interrupt_type: str
    status: str
    created_at: datetime
    resolved_at: datetime | None
    resolved_by_user_id: UUID | None
    resume_payload: dict[str, Any] | None
    metadata: dict[str, Any] | None


class HITLRepository(Protocol):
    """Repository port for HITL persistence."""

    async def create_interrupt(self, interrupt: WorkflowInterrupt) -> WorkflowInterrupt:
        """Create workflow interrupt."""
        ...

    async def get_interrupt(self, interrupt_id: UUID) -> WorkflowInterrupt | None:
        """Get interrupt by ID."""
        ...

    async def get_by_approval(self, approval_id: str) -> WorkflowInterrupt | None:
        """Get interrupt by approval ID."""
        ...

    async def update_interrupt(self, interrupt: WorkflowInterrupt) -> WorkflowInterrupt:
        """Update interrupt."""
        ...

    async def list_waiting(
        self, customer_id: str | None = None
    ) -> list[WorkflowInterrupt]:
        """List waiting interrupts."""
        ...
