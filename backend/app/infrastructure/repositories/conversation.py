"""Conversation repository implementation."""

from __future__ import annotations

import json
from uuid import UUID

from app.domain.conversation.entities import Conversation, Message
from app.infrastructure.database.postgres import PostgresDatabase


class PostgresConversationRepository:
    """PostgreSQL implementation of ConversationRepository port."""

    def __init__(self, db: PostgresDatabase) -> None:
        self.db = db

    async def create(self, conversation: Conversation) -> Conversation:
        row = await self.db.fetchrow(
            """
            INSERT INTO conversations (conversation_id, customer_id, title, status, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            conversation.conversation_id,
            conversation.customer_id,
            conversation.title,
            conversation.status,
            json.dumps(conversation.metadata) if conversation.metadata else None,
        )
        assert row is not None
        return _row_to_conversation(row)

    async def get(self, conversation_id: UUID) -> Conversation | None:
        row = await self.db.fetchrow(
            "SELECT * FROM conversations WHERE conversation_id = $1",
            conversation_id,
        )
        if row is None:
            return None
        return _row_to_conversation(row)

    async def update(self, conversation: Conversation) -> Conversation:
        row = await self.db.fetchrow(
            """
            UPDATE conversations
            SET title = $2, status = $3, completed_at = $4, metadata = $5, updated_at = NOW()
            WHERE conversation_id = $1
            RETURNING *
            """,
            conversation.conversation_id,
            conversation.title,
            conversation.status,
            conversation.completed_at,
            json.dumps(conversation.metadata) if conversation.metadata else None,
        )
        assert row is not None
        return _row_to_conversation(row)

    async def add_message(self, message: Message) -> Message:
        row = await self.db.fetchrow(
            """
            INSERT INTO messages
                (message_id, conversation_id, role, content, metadata, tool_calls, tool_call_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            message.message_id,
            message.conversation_id,
            message.role,
            message.content,
            json.dumps(message.metadata) if message.metadata else None,
            json.dumps(message.tool_calls) if message.tool_calls else None,
            message.tool_call_id,
        )
        assert row is not None
        return _row_to_message(row)

    async def has_assistant_message_for_run(self, conversation_id: UUID, run_id: UUID) -> bool:
        return bool(
            await self.db.fetchval(
                """SELECT EXISTS(
                    SELECT 1 FROM messages
                    WHERE conversation_id = $1 AND role = 'assistant'
                      AND metadata->>'run_id' = $2
                )""",
                conversation_id,
                str(run_id),
            )
        )

    async def get_messages(self, conversation_id: UUID, limit: int | None = None) -> list[Message]:
        if limit:
            rows = await self.db.fetch(
                """
                SELECT * FROM (
                    SELECT * FROM messages WHERE conversation_id = $1
                    ORDER BY created_at DESC LIMIT $2
                ) sub ORDER BY created_at ASC
                """,
                conversation_id,
                limit,
            )
        else:
            rows = await self.db.fetch(
                "SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at ASC",
                conversation_id,
            )
        return [_row_to_message(r) for r in rows]

    async def list_customer_conversations(self, customer_id: str, limit: int = 50) -> list[Conversation]:
        rows = await self.db.fetch(
            "SELECT * FROM conversations WHERE customer_id = $1 ORDER BY created_at DESC LIMIT $2",
            customer_id,
            limit,
        )
        return [_row_to_conversation(r) for r in rows]


def _row_to_conversation(row: object) -> Conversation:
    metadata = row["metadata"]  # type: ignore[index]
    return Conversation(
        conversation_id=row["conversation_id"],  # type: ignore[index]
        customer_id=row["customer_id"],  # type: ignore[index]
        title=row["title"],  # type: ignore[index]
        status=row["status"],  # type: ignore[index]
        created_at=row["created_at"],  # type: ignore[index]
        updated_at=row["updated_at"],  # type: ignore[index]
        completed_at=row["completed_at"],  # type: ignore[index]
        metadata=json.loads(metadata) if isinstance(metadata, str) else metadata,
    )


def _row_to_message(row: object) -> Message:
    metadata = row["metadata"]  # type: ignore[index]
    tool_calls = row["tool_calls"]  # type: ignore[index]
    return Message(
        message_id=row["message_id"],  # type: ignore[index]
        conversation_id=row["conversation_id"],  # type: ignore[index]
        role=row["role"],  # type: ignore[index]
        content=row["content"],  # type: ignore[index]
        created_at=row["created_at"],  # type: ignore[index]
        metadata=json.loads(metadata) if isinstance(metadata, str) else metadata,
        tool_calls=json.loads(tool_calls) if isinstance(tool_calls, str) else tool_calls,
        tool_call_id=row["tool_call_id"],  # type: ignore[index]
    )
