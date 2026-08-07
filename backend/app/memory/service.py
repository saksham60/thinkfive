"""Memory service - orchestrates extraction, policy enforcement, and retrieval."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.core.constants import MemoryStatus
from app.domain.memory.entities import CustomerMemory
from app.memory.extractor import MemoryExtractor
from app.memory.policy import MemoryPolicyEnforcer
from app.memory.summarizer import ConversationSummarizer

if TYPE_CHECKING:
    from app.domain.conversation.entities import Message
    from app.infrastructure.repositories.memory import PostgresMemoryRepository

logger = logging.getLogger(__name__)


class MemoryService:
    """Coordinates the three memory layers: graph checkpoint (external), conversation
    persistence (external), and long-term customer memory (owned here).

    Write flow: candidate -> extraction -> PII/secret check -> MemoryPolicy -> repository.
    """

    def __init__(
        self,
        memory_repo: PostgresMemoryRepository,
        extractor: MemoryExtractor,
        policy_enforcer: MemoryPolicyEnforcer,
        summarizer: ConversationSummarizer,
        ttl_days: int = 90,
    ) -> None:
        self.memory_repo = memory_repo
        self.extractor = extractor
        self.policy_enforcer = policy_enforcer
        self.summarizer = summarizer
        self.ttl_days = ttl_days

    async def process_user_message(
        self,
        customer_id: str,
        user_message: str,
        conversation_id: UUID,
        message_id: UUID,
    ) -> list[CustomerMemory]:
        """Extract candidate memories, enforce policy, and persist allowed ones."""
        from datetime import datetime, timedelta

        candidates = self.extractor.extract(user_message)
        stored: list[CustomerMemory] = []

        for candidate in candidates:
            if not self.policy_enforcer.can_store(candidate):
                logger.info(f"Memory candidate rejected by policy: {candidate.memory_type}")
                continue

            memory = CustomerMemory(
                memory_id=uuid4(),
                customer_id=customer_id,
                memory_type=candidate.memory_type,
                memory_key=candidate.memory_key,
                content=candidate.content,
                structured_value=candidate.structured_value,
                source_conversation_id=conversation_id,
                source_message_id=message_id,
                confidence=candidate.confidence,
                status=MemoryStatus.ACTIVE.value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=self.ttl_days),
                metadata=None,
            )
            saved = await self.memory_repo.store_memory(memory)
            stored.append(saved)

        return stored

    async def get_memory_context(self, customer_id: str) -> dict[str, object]:
        """Retrieve active memories to surface as context (customer isolation enforced by query)."""
        memories = await self.memory_repo.get_active_memories(customer_id)
        context: dict[str, object] = {}
        for m in memories:
            if m.memory_key:
                context[m.memory_key] = m.content
        return context

    async def maybe_summarize(
        self,
        conversation_id: UUID,
        customer_id: str,
        messages: list[Message],
        threshold: int,
    ) -> str | None:
        """Summarize if threshold exceeded. Original messages remain persisted untouched."""
        if not self.summarizer.should_summarize(len(messages), threshold):
            return None

        summary_text = await self.summarizer.summarize(messages)

        from datetime import datetime

        from app.domain.memory.entities import ConversationSummary

        summary = ConversationSummary(
            conversation_id=conversation_id,
            customer_id=customer_id,
            summary=summary_text,
            message_count=len(messages),
            created_at=datetime.utcnow(),
        )
        await self.memory_repo.store_summary(summary)
        return summary_text
