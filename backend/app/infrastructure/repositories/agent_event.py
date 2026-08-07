"""Agent event repository implementation (SSE persistence + replay source)."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from app.infrastructure.database.postgres import PostgresDatabase


class AgentEventRepository:
    """Repository for agent_events table - source of truth for SSE replay."""

    def __init__(self, db: PostgresDatabase) -> None:
        self.db = db

    async def append(
        self,
        run_id: UUID,
        conversation_id: UUID,
        customer_id: str,
        event_type: str,
        agent_name: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        duration_ms: float | None = None,
        correlation_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist an event and return it with its monotonic event_seq."""
        row = await self.db.fetchrow(
            """
            INSERT INTO agent_events
                (event_id, run_id, conversation_id, customer_id, event_type,
                 agent_name, tool_name, status, duration_ms, correlation_id, payload)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
            """,
            uuid4(),
            run_id,
            conversation_id,
            customer_id,
            event_type,
            agent_name,
            tool_name,
            status,
            duration_ms,
            correlation_id,
            json.dumps(payload) if payload else None,
        )
        assert row is not None
        return dict(row)

    async def get_since(
        self,
        conversation_id: UUID,
        after_seq: int = 0,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Get events for replay after a given event_seq (Last-Event-ID)."""
        rows = await self.db.fetch(
            """
            SELECT * FROM agent_events
            WHERE conversation_id = $1 AND event_seq > $2
            ORDER BY event_seq ASC LIMIT $3
            """,
            conversation_id,
            after_seq,
            limit,
        )
        return [dict(r) for r in rows]

    async def get_run_events(self, run_id: UUID) -> list[dict[str, Any]]:
        rows = await self.db.fetch(
            "SELECT * FROM agent_events WHERE run_id = $1 ORDER BY event_seq ASC",
            run_id,
        )
        return [dict(r) for r in rows]

    async def count_by_type(self, since: object = None) -> dict[str, int]:
        rows = await self.db.fetch(
            "SELECT event_type, COUNT(*) as cnt FROM agent_events GROUP BY event_type",
        )
        return {r["event_type"]: r["cnt"] for r in rows}
