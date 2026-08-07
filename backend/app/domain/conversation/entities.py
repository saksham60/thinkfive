"""Conversation domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID


@dataclass
class Message:
    """Conversation message entity."""

    message_id: UUID
    conversation_id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, object] | None = None
    tool_calls: list[dict[str, object]] | None = None
    tool_call_id: str | None = None


@dataclass
class Conversation:
    """Conversation entity."""

    conversation_id: UUID
    customer_id: str
    title: str | None = None
    status: Literal["active", "completed", "failed"] = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, object] | None = None
    messages: list[Message] = field(default_factory=list)


class ConversationRepository(Protocol):
    """Repository port for conversation persistence."""

    async def create(self, conversation: Conversation) -> Conversation:
        """Create new conversation."""
        ...

    async def get(self, conversation_id: UUID) -> Conversation | None:
        """Retrieve conversation by ID."""
        ...

    async def update(self, conversation: Conversation) -> Conversation:
        """Update conversation."""
        ...

    async def add_message(self, message: Message) -> Message:
        """Add message to conversation."""
        ...

    async def get_messages(
        self, conversation_id: UUID, limit: int | None = None
    ) -> list[Message]:
        """Get conversation messages."""
        ...

    async def list_customer_conversations(
        self, customer_id: str, limit: int = 50
    ) -> list[Conversation]:
        """List conversations for customer."""
        ...
