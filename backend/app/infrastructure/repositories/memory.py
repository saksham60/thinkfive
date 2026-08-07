"""Customer memory repository implementation."""

from __future__ import annotations

import json
from uuid import UUID

from app.domain.memory.entities import ConversationSummary, CustomerMemory
from app.infrastructure.database.postgres import PostgresDatabase


class PostgresMemoryRepository:
    """PostgreSQL implementation of MemoryRepository port."""

    def __init__(self, db: PostgresDatabase) -> None:
        self.db = db

    async def store_memory(self, memory: CustomerMemory) -> CustomerMemory:
        row = await self.db.fetchrow(
            """
            INSERT INTO customer_memories
                (memory_id, customer_id, memory_type, memory_key, content, structured_value,
                 source_conversation_id, source_message_id, confidence, status, expires_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
            """,
            memory.memory_id,
            memory.customer_id,
            memory.memory_type,
            memory.memory_key,
            memory.content,
            json.dumps(memory.structured_value) if memory.structured_value else None,
            memory.source_conversation_id,
            memory.source_message_id,
            memory.confidence,
            memory.status,
            memory.expires_at,
            json.dumps(memory.metadata) if memory.metadata else None,
        )
        assert row is not None
        return _row_to_memory(row)

    async def get_active_memories(
        self,
        customer_id: str,
        memory_type: str | None = None,
        limit: int = 50,
    ) -> list[CustomerMemory]:
        if memory_type:
            rows = await self.db.fetch(
                """
                SELECT * FROM customer_memories
                WHERE customer_id = $1 AND status = 'ACTIVE' AND memory_type = $2
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY created_at DESC LIMIT $3
                """,
                customer_id,
                memory_type,
                limit,
            )
        else:
            rows = await self.db.fetch(
                """
                SELECT * FROM customer_memories
                WHERE customer_id = $1 AND status = 'ACTIVE'
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY created_at DESC LIMIT $2
                """,
                customer_id,
                limit,
            )
        return [_row_to_memory(r) for r in rows]

    async def expire_memory(self, memory_id: UUID) -> None:
        await self.db.execute(
            "UPDATE customer_memories SET status = 'EXPIRED', updated_at = NOW() WHERE memory_id = $1",
            memory_id,
        )

    async def store_summary(self, summary: ConversationSummary) -> ConversationSummary:
        row = await self.db.fetchrow(
            """
            INSERT INTO conversation_summaries (conversation_id, customer_id, summary, message_count, metadata)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (conversation_id) DO UPDATE
                SET summary = $3, message_count = $4, metadata = $5
            RETURNING *
            """,
            summary.conversation_id,
            summary.customer_id,
            summary.summary,
            summary.message_count,
            json.dumps(summary.metadata) if summary.metadata else None,
        )
        assert row is not None
        return _row_to_summary(row)

    async def get_summary(self, conversation_id: UUID) -> ConversationSummary | None:
        row = await self.db.fetchrow(
            "SELECT * FROM conversation_summaries WHERE conversation_id = $1",
            conversation_id,
        )
        if row is None:
            return None
        return _row_to_summary(row)


def _row_to_memory(row: object) -> CustomerMemory:
    structured_value = row["structured_value"]  # type: ignore[index]
    metadata = row["metadata"]  # type: ignore[index]
    return CustomerMemory(
        memory_id=row["memory_id"],  # type: ignore[index]
        customer_id=row["customer_id"],  # type: ignore[index]
        memory_type=row["memory_type"],  # type: ignore[index]
        memory_key=row["memory_key"],  # type: ignore[index]
        content=row["content"],  # type: ignore[index]
        structured_value=json.loads(structured_value) if isinstance(structured_value, str) else structured_value,
        source_conversation_id=row["source_conversation_id"],  # type: ignore[index]
        source_message_id=row["source_message_id"],  # type: ignore[index]
        confidence=row["confidence"],  # type: ignore[index]
        status=row["status"],  # type: ignore[index]
        created_at=row["created_at"],  # type: ignore[index]
        updated_at=row["updated_at"],  # type: ignore[index]
        expires_at=row["expires_at"],  # type: ignore[index]
        metadata=json.loads(metadata) if isinstance(metadata, str) else metadata,
    )


def _row_to_summary(row: object) -> ConversationSummary:
    metadata = row["metadata"]  # type: ignore[index]
    return ConversationSummary(
        conversation_id=row["conversation_id"],  # type: ignore[index]
        customer_id=row["customer_id"],  # type: ignore[index]
        summary=row["summary"],  # type: ignore[index]
        message_count=row["message_count"],  # type: ignore[index]
        created_at=row["created_at"],  # type: ignore[index]
        metadata=json.loads(metadata) if isinstance(metadata, str) else metadata,
    )
