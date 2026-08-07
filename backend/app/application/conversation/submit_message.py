"""Use case: submit a chat message (async graph execution trigger)."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from app.core.constants import EventType
from app.domain.conversation.entities import Conversation, Message

if TYPE_CHECKING:
    from app.agents.graph.runner import GraphRunner
    from app.events.publisher import EventPublisher
    from app.infrastructure.repositories.agent_run import AgentRunRepository
    from app.infrastructure.repositories.conversation import PostgresConversationRepository
    from app.memory.service import MemoryService

logger = logging.getLogger(__name__)


class SubmitMessageUseCase:
    """Submits a customer message: persists it, queues run, returns immediately.

    Graph execution happens as a background asyncio task; progress is
    communicated to the client exclusively via SSE.
    """

    def __init__(
        self,
        conversation_repo: PostgresConversationRepository,
        agent_run_repo: AgentRunRepository,
        graph_runner: GraphRunner,
        event_publisher: EventPublisher,
        memory_service: MemoryService,
        runtime_context_factory: Any,
    ) -> None:
        self.conversation_repo = conversation_repo
        self.agent_run_repo = agent_run_repo
        self.graph_runner = graph_runner
        self.event_publisher = event_publisher
        self.memory_service = memory_service
        self.runtime_context_factory = runtime_context_factory

    async def execute(
        self,
        customer_id: str,
        message: str,
        conversation_id: UUID | None = None,
    ) -> dict[str, Any]:
        # Get or create conversation
        if conversation_id is not None:
            conversation = await self.conversation_repo.get(conversation_id)
            if conversation is None:
                raise ValueError(f"Conversation {conversation_id} not found")
        else:
            conversation = Conversation(conversation_id=uuid4(), customer_id=customer_id, status="active")
            conversation = await self.conversation_repo.create(conversation)

        # Persist user message (conversation memory layer)
        user_message = Message(
            message_id=uuid4(),
            conversation_id=conversation.conversation_id,
            role="user",
            content=message,
        )
        saved_message = await self.conversation_repo.add_message(user_message)

        # Extract + policy-check long-term memory candidates (does not block the response)
        await self.memory_service.process_user_message(
            customer_id, message, conversation.conversation_id, saved_message.message_id
        )

        # thread_id maps 1:1 to conversation_id for LangGraph checkpointing
        thread_id = str(conversation.conversation_id)
        run_id = await self.agent_run_repo.create(
            conversation_id=conversation.conversation_id,
            customer_id=customer_id,
            thread_id=thread_id,
        )

        await self.event_publisher.publish(
            conversation.conversation_id,
            EventType.CHAT_ACCEPTED,
            {"run_id": str(run_id), "conversation_id": str(conversation.conversation_id)},
            run_id=run_id,
            customer_id=customer_id,
        )

        runtime_context = self.runtime_context_factory(customer_id)

        # Bounded conversation context plus durable customer memory. Live MCP
        # results remain authoritative and are collected later by specialists.
        all_messages = await self.conversation_repo.get_messages(conversation.conversation_id)
        summary = await self.memory_service.maybe_summarize(
            conversation.conversation_id,
            customer_id,
            all_messages,
            self.graph_runner.summary_threshold,
        )
        if summary is None:
            stored_summary = await self.memory_service.memory_repo.get_summary(conversation.conversation_id)
            summary = stored_summary.summary if stored_summary else None
        recent_messages = all_messages[-self.graph_runner.recent_message_limit :]
        memory_context = await self.memory_service.get_memory_context(customer_id)

        # Fire-and-forget background execution; SSE carries all further progress.
        asyncio.create_task(
            self.graph_runner.start_run(
                run_id=run_id,
                conversation_id=conversation.conversation_id,
                thread_id=thread_id,
                customer_id=customer_id,
                message=message,
                runtime_context=runtime_context,
                conversation_messages=recent_messages,
                conversation_summary=summary,
                memory_context=memory_context,
            )
        )

        return {
            "conversation_id": str(conversation.conversation_id),
            "run_id": str(run_id),
            "status": "QUEUED",
        }
