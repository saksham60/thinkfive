"""Memory domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass
class CustomerMemory:
    """Customer long-term memory entity."""

    memory_id: UUID
    customer_id: str
    memory_type: str
    memory_key: str | None
    content: str | None
    structured_value: dict[str, Any] | None
    source_conversation_id: UUID | None
    source_message_id: UUID | None
    confidence: float | None
    status: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    metadata: dict[str, Any] | None


@dataclass
class ConversationSummary:
    """Conversation summary for memory."""

    conversation_id: UUID
    customer_id: str
    summary: str
    message_count: int
    created_at: datetime
    metadata: dict[str, Any] | None = None


class MemoryRepository(Protocol):
    """Repository port for memory persistence."""

    async def store_memory(self, memory: CustomerMemory) -> CustomerMemory:
        """Store customer memory."""
        ...

    async def get_active_memories(
        self,
        customer_id: str,
        memory_type: str | None = None,
        limit: int = 50,
    ) -> list[CustomerMemory]:
        """Get active memories for customer."""
        ...

    async def expire_memory(self, memory_id: UUID) -> None:
        """Mark memory as expired."""
        ...

    async def store_summary(self, summary: ConversationSummary) -> ConversationSummary:
        """Store conversation summary."""
        ...

    async def get_summary(self, conversation_id: UUID) -> ConversationSummary | None:
        """Get conversation summary."""
        ...
