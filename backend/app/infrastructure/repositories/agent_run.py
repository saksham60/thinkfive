"""Agent run repository implementation."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.core.constants import RunStatus
from app.infrastructure.database.postgres import PostgresDatabase


class AgentRunRepository:
    """Repository for agent_runs table."""

    def __init__(self, db: PostgresDatabase) -> None:
        self.db = db

    async def create(
        self,
        conversation_id: UUID,
        customer_id: str,
        thread_id: str,
        model: str | None = None,
        provider: str | None = None,
    ) -> UUID:
        run_id = uuid4()
        await self.db.execute(
            """
            INSERT INTO agent_runs
                (run_id, conversation_id, customer_id, thread_id, status, model, provider, started_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """,
            run_id,
            conversation_id,
            customer_id,
            thread_id,
            RunStatus.QUEUED.value,
            model,
            provider,
        )
        return run_id

    async def update_status(
        self,
        run_id: UUID,
        status: RunStatus,
        error_message: str | None = None,
        token_usage: dict[str, Any] | None = None,
        cost_usd: float | None = None,
    ) -> None:
        completed = status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.INTERRUPTED)
        await self.db.execute(
            """
            UPDATE agent_runs
            SET status = $2,
                error_message = COALESCE($3, error_message),
                token_usage = COALESCE($4, token_usage),
                cost_usd = COALESCE($5, cost_usd),
                completed_at = CASE WHEN $6 THEN NOW() ELSE completed_at END,
                duration_ms = CASE WHEN $6 THEN EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000 ELSE duration_ms END
            WHERE run_id = $1
            """,
            run_id,
            status.value,
            error_message,
            json.dumps(token_usage) if token_usage else None,
            cost_usd,
            completed,
        )

    async def get(self, run_id: UUID) -> dict[str, Any] | None:
        row = await self.db.fetchrow("SELECT * FROM agent_runs WHERE run_id = $1", run_id)
        return dict(row) if row else None

    async def find_stale_runs(self) -> list[dict[str, Any]]:
        """Find QUEUED/RUNNING runs from a previous process (for restart recovery)."""
        rows = await self.db.fetch(
            "SELECT * FROM agent_runs WHERE status IN ('QUEUED', 'RUNNING')",
        )
        return [dict(r) for r in rows]

    async def mark_interrupted(self, run_id: UUID) -> None:
        await self.db.execute(
            "UPDATE agent_runs SET status = 'INTERRUPTED' WHERE run_id = $1 AND status IN ('QUEUED', 'RUNNING')",
            run_id,
        )

    async def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = await self.db.fetch(
            "SELECT * FROM agent_runs ORDER BY created_at DESC LIMIT $1", limit
        )
        return [dict(r) for r in rows]

    async def get_metrics(self, since: datetime | None = None) -> dict[str, Any]:
        """Compute run metrics for supervisor observability."""
        where_clause = "WHERE created_at >= $1" if since else ""
        params = [since] if since else []

        row = await self.db.fetchrow(
            f"""
            SELECT
                COUNT(*) AS total_runs,
                COUNT(*) FILTER (WHERE status = 'COMPLETED') AS completed_runs,
                COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_runs,
                COUNT(*) FILTER (WHERE status = 'WAITING_FOR_HUMAN') AS waiting_runs,
                AVG(duration_ms) FILTER (WHERE duration_ms IS NOT NULL) AS avg_latency_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_latency_ms
            FROM agent_runs {where_clause}
            """,
            *params,
        )
        return dict(row) if row else {}
