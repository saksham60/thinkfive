"""Conversation domain events."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ConversationStarted:
    """Conversation started event."""

    conversation_id: UUID
    customer_id: str
    timestamp: datetime


@dataclass(frozen=True)
class MessageAdded:
    """Message added to conversation event."""

    conversation_id: UUID
    message_id: UUID
    role: str
    timestamp: datetime


@dataclass(frozen=True)
class ConversationCompleted:
    """Conversation completed event."""

    conversation_id: UUID
    timestamp: datetime
