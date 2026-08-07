"""Use case: get conversation history."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.domain.conversation.entities import Message
    from app.infrastructure.repositories.conversation import PostgresConversationRepository


class GetHistoryUseCase:
    """Retrieves conversation messages for display/audit."""

    def __init__(self, conversation_repo: PostgresConversationRepository) -> None:
        self.conversation_repo = conversation_repo

    async def execute(self, conversation_id: UUID) -> list[Message]:
        return await self.conversation_repo.get_messages(conversation_id)
