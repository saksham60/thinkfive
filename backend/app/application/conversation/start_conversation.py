"""Use case: start a new conversation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from app.domain.conversation.entities import Conversation

if TYPE_CHECKING:
    from app.infrastructure.repositories.conversation import PostgresConversationRepository


class StartConversationUseCase:
    """Creates a new conversation for a customer."""

    def __init__(self, conversation_repo: PostgresConversationRepository) -> None:
        self.conversation_repo = conversation_repo

    async def execute(self, customer_id: str, title: str | None = None) -> Conversation:
        conversation = Conversation(
            conversation_id=uuid4(),
            customer_id=customer_id,
            title=title,
            status="active",
        )
        return await self.conversation_repo.create(conversation)
