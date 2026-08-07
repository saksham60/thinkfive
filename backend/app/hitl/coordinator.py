"""HITL coordinator - correlates run/conversation/case/approval and manages waiting state."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from app.core.constants import InterruptStatus
from app.domain.hitl.entities import WorkflowInterrupt

if TYPE_CHECKING:
    from app.infrastructure.repositories.policy import PostgresHITLRepository

logger = logging.getLogger(__name__)


class HITLCoordinator:
    """Manages workflow_interrupts persistence - backend orchestration correlation only.

    Does NOT duplicate Case MCP approval authority; only tracks which
    LangGraph thread is waiting on which approval_id so it can be resumed.
    """

    def __init__(self, hitl_repo: PostgresHITLRepository) -> None:
        self.hitl_repo = hitl_repo

    async def record_waiting(
        self,
        run_id: UUID,
        conversation_id: UUID,
        thread_id: str,
        customer_id: str | None,
        case_id: str | None,
        approval_id: str | None,
        interrupt_type: str = "approval",
    ) -> WorkflowInterrupt:
        interrupt = WorkflowInterrupt(
            interrupt_id=uuid4(),
            run_id=run_id,
            conversation_id=conversation_id,
            thread_id=thread_id,
            customer_id=customer_id,
            case_id=case_id,
            approval_id=approval_id,
            interrupt_type=interrupt_type,
            status=InterruptStatus.WAITING.value,
            created_at=datetime.utcnow(),
            resolved_at=None,
            resolved_by_user_id=None,
            resume_payload=None,
            metadata=None,
        )
        return await self.hitl_repo.create_interrupt(interrupt)

    async def find_waiting_by_approval(self, approval_id: str) -> WorkflowInterrupt | None:
        return await self.hitl_repo.get_by_approval(approval_id)

    async def mark_resolved(
        self,
        interrupt_id: UUID,
        status: InterruptStatus,
        resolved_by_user_id: UUID,
        resume_payload: dict[str, Any],
    ) -> WorkflowInterrupt:
        interrupt = await self.hitl_repo.get_interrupt(interrupt_id)
        if interrupt is None:
            raise ValueError(f"Interrupt {interrupt_id} not found")

        interrupt.status = status.value
        interrupt.resolved_at = datetime.utcnow()
        interrupt.resolved_by_user_id = resolved_by_user_id
        interrupt.resume_payload = resume_payload
        return await self.hitl_repo.update_interrupt(interrupt)

    async def list_waiting(self, customer_id: str | None = None) -> list[WorkflowInterrupt]:
        return await self.hitl_repo.list_waiting(customer_id)
