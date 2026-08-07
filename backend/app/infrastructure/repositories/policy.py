"""Workflow interrupt (HITL) repository implementation."""

from __future__ import annotations

import json
from uuid import UUID

from app.domain.hitl.entities import WorkflowInterrupt
from app.infrastructure.database.postgres import PostgresDatabase


class PostgresHITLRepository:
    """PostgreSQL implementation of HITLRepository port."""

    def __init__(self, db: PostgresDatabase) -> None:
        self.db = db

    async def create_interrupt(self, interrupt: WorkflowInterrupt) -> WorkflowInterrupt:
        row = await self.db.fetchrow(
            """
            INSERT INTO workflow_interrupts
                (interrupt_id, run_id, conversation_id, thread_id, customer_id,
                 case_id, approval_id, interrupt_type, status, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
            """,
            interrupt.interrupt_id,
            interrupt.run_id,
            interrupt.conversation_id,
            interrupt.thread_id,
            interrupt.customer_id,
            interrupt.case_id,
            interrupt.approval_id,
            interrupt.interrupt_type,
            interrupt.status,
            json.dumps(interrupt.metadata) if interrupt.metadata else None,
        )
        assert row is not None
        return _row_to_interrupt(row)

    async def get_interrupt(self, interrupt_id: UUID) -> WorkflowInterrupt | None:
        row = await self.db.fetchrow(
            "SELECT * FROM workflow_interrupts WHERE interrupt_id = $1", interrupt_id
        )
        return _row_to_interrupt(row) if row else None

    async def get_by_approval(self, approval_id: str) -> WorkflowInterrupt | None:
        row = await self.db.fetchrow(
            "SELECT * FROM workflow_interrupts WHERE approval_id = $1 ORDER BY created_at DESC LIMIT 1",
            approval_id,
        )
        return _row_to_interrupt(row) if row else None

    async def update_interrupt(self, interrupt: WorkflowInterrupt) -> WorkflowInterrupt:
        row = await self.db.fetchrow(
            """
            UPDATE workflow_interrupts
            SET status = $2, resolved_at = $3, resolved_by_user_id = $4,
                resume_payload = $5, metadata = $6
            WHERE interrupt_id = $1
            RETURNING *
            """,
            interrupt.interrupt_id,
            interrupt.status,
            interrupt.resolved_at,
            interrupt.resolved_by_user_id,
            json.dumps(interrupt.resume_payload) if interrupt.resume_payload else None,
            json.dumps(interrupt.metadata) if interrupt.metadata else None,
        )
        assert row is not None
        return _row_to_interrupt(row)

    async def list_waiting(self, customer_id: str | None = None) -> list[WorkflowInterrupt]:
        if customer_id:
            rows = await self.db.fetch(
                "SELECT * FROM workflow_interrupts WHERE status = 'WAITING' AND customer_id = $1",
                customer_id,
            )
        else:
            rows = await self.db.fetch("SELECT * FROM workflow_interrupts WHERE status = 'WAITING'")
        return [_row_to_interrupt(r) for r in rows]


def _row_to_interrupt(row: object) -> WorkflowInterrupt:
    resume_payload = row["resume_payload"]  # type: ignore[index]
    metadata = row["metadata"]  # type: ignore[index]
    return WorkflowInterrupt(
        interrupt_id=row["interrupt_id"],  # type: ignore[index]
        run_id=row["run_id"],  # type: ignore[index]
        conversation_id=row["conversation_id"],  # type: ignore[index]
        thread_id=row["thread_id"],  # type: ignore[index]
        customer_id=row["customer_id"],  # type: ignore[index]
        case_id=row["case_id"],  # type: ignore[index]
        approval_id=row["approval_id"],  # type: ignore[index]
        interrupt_type=row["interrupt_type"],  # type: ignore[index]
        status=row["status"],  # type: ignore[index]
        created_at=row["created_at"],  # type: ignore[index]
        resolved_at=row["resolved_at"],  # type: ignore[index]
        resolved_by_user_id=row["resolved_by_user_id"],  # type: ignore[index]
        resume_payload=json.loads(resume_payload) if isinstance(resume_payload, str) else resume_payload,
        metadata=json.loads(metadata) if isinstance(metadata, str) else metadata,
    )
