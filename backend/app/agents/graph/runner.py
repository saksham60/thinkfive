"""LangGraph runner - executes the graph with checkpointing and event publishing."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.types import Command

from app.core.constants import EventType, RunStatus

logger = logging.getLogger(__name__)


class GraphRunner:
    """Executes the compiled LangGraph, persisting run/event state and publishing SSE."""

    def __init__(
        self,
        graph: Any,
        agent_run_repo: Any,
        agent_event_repo: Any,
        event_publisher: Any,
        hitl_coordinator: Any,
        conversation_repo: Any,
        memory_service: Any,
        max_iterations: int = 15,
        recent_message_limit: int = 10,
        summary_threshold: int = 20,
    ) -> None:
        self.graph = graph
        self.agent_run_repo = agent_run_repo
        self.agent_event_repo = agent_event_repo
        self.event_publisher = event_publisher
        self.hitl_coordinator = hitl_coordinator
        self.conversation_repo = conversation_repo
        self.memory_service = memory_service
        self.max_iterations = max_iterations
        self.recent_message_limit = recent_message_limit
        self.summary_threshold = summary_threshold

    async def start_run(
        self,
        run_id: UUID,
        conversation_id: UUID,
        thread_id: str,
        customer_id: str,
        message: str,
        runtime_context: dict[str, Any],
        conversation_messages: list[Any] | None = None,
        conversation_summary: str | None = None,
        memory_context: dict[str, Any] | None = None,
    ) -> None:
        """Start a new graph run (called from a background task after chat.accepted)."""
        await self.agent_run_repo.update_status(run_id, RunStatus.RUNNING)
        await self.event_publisher.publish(conversation_id, EventType.AGENT_STARTED,
            {"run_id": str(run_id), "conversation_id": str(conversation_id), "customer_id": customer_id},
            run_id=run_id, customer_id=customer_id)

        config = {
            "configurable": {
                "thread_id": thread_id,
                "customer_id": customer_id,
                "max_iterations": self.max_iterations,
                **runtime_context,
            },
            "recursion_limit": self.max_iterations * 4,
        }

        history: list[BaseMessage] = []
        if conversation_summary:
            history.append(SystemMessage(content=f"Conversation summary: {conversation_summary}"))
        for item in conversation_messages or []:
            if item.role == "user":
                history.append(HumanMessage(content=item.content))
            elif item.role == "assistant":
                history.append(AIMessage(content=item.content))
        if not history or not isinstance(history[-1], HumanMessage) or history[-1].content != message:
            history.append(HumanMessage(content=message))

        initial_state = {
            "messages": history,
            "conversation_id": str(conversation_id),
            "run_id": str(run_id),
            "thread_id": thread_id,
            "customer_id": customer_id,
            "memory_context": memory_context or {},
            "iteration_count": 0,
            "warnings": [],
            "errors": [],
        }

        try:
            result = await self.graph.ainvoke(initial_state, config=config)

            # Detect interrupt (graph paused waiting for human)
            snapshot = await self.graph.aget_state(config)
            if snapshot.next:
                values = snapshot.values or {}
                pending = values.get("pending_human_action") or {}
                approval_id = pending.get("approval_id")
                case_id = pending.get("case_id")
                if approval_id:
                    existing = await self.hitl_coordinator.find_waiting_by_approval(approval_id)
                    if existing is None:
                        await self.hitl_coordinator.record_waiting(
                            run_id, conversation_id, thread_id, customer_id, case_id, approval_id
                        )
                await self.agent_run_repo.update_status(run_id, RunStatus.WAITING_FOR_HUMAN)
                await self.event_publisher.publish(
                    conversation_id, EventType.APPROVAL_REQUESTED,
                    {"run_id": str(run_id), "conversation_id": str(conversation_id),
                     "customer_id": customer_id, "case_id": case_id, "approval_id": approval_id},
                    run_id=run_id, customer_id=customer_id,
                )
                await self.event_publisher.publish(
                    conversation_id,
                    EventType.WORKFLOW_INTERRUPTED,
                    {"run_id": str(run_id), "conversation_id": str(conversation_id),
                     "customer_id": customer_id, "case_id": case_id, "approval_id": approval_id},
                    run_id=run_id, customer_id=customer_id,
                )
                return

            final_response = result.get("final_response", "")
            await self._persist_final_response(run_id, conversation_id, customer_id, final_response)
            await self.agent_run_repo.update_status(run_id, RunStatus.COMPLETED)
            await self.event_publisher.publish(
                conversation_id,
                EventType.CHAT_COMPLETED,
                {"run_id": str(run_id), "conversation_id": str(conversation_id),
                 "customer_id": customer_id, "response": final_response},
                run_id=run_id, customer_id=customer_id,
            )

        except Exception as e:
            logger.error(f"Graph run {run_id} failed: {e}")
            await self.agent_run_repo.update_status(run_id, RunStatus.FAILED, error_message=str(e))
            await self.event_publisher.publish(
                conversation_id, EventType.CHAT_FAILED,
                {"run_id": str(run_id), "conversation_id": str(conversation_id),
                 "customer_id": customer_id, "error": str(e)},
                run_id=run_id, customer_id=customer_id,
            )

    async def resume_run(
        self,
        run_id: UUID,
        conversation_id: UUID,
        thread_id: str,
        resume_payload: dict[str, Any],
        runtime_context: dict[str, Any],
        customer_id: str,
    ) -> None:
        """Resume a graph paused at a HITL interrupt using Command(resume=...)."""
        config = {
            "configurable": {
                "thread_id": thread_id,
                "customer_id": customer_id,
                "max_iterations": self.max_iterations,
                **runtime_context,
            },
            "recursion_limit": self.max_iterations * 4,
        }

        await self.agent_run_repo.update_status(run_id, RunStatus.RUNNING)
        await self.event_publisher.publish(
            conversation_id, EventType.WORKFLOW_RESUMED,
            {"run_id": str(run_id), "conversation_id": str(conversation_id), "customer_id": customer_id},
            run_id=run_id, customer_id=customer_id,
        )

        try:
            result = await self.graph.ainvoke(Command(resume=resume_payload), config=config)

            snapshot = await self.graph.aget_state(config)
            if snapshot.next:
                values = snapshot.values or {}
                pending = values.get("pending_human_action") or {}
                approval_id = pending.get("approval_id")
                case_id = pending.get("case_id")
                if approval_id and await self.hitl_coordinator.find_waiting_by_approval(approval_id) is None:
                    await self.hitl_coordinator.record_waiting(
                        run_id, conversation_id, thread_id, customer_id, case_id, approval_id
                    )
                await self.agent_run_repo.update_status(run_id, RunStatus.WAITING_FOR_HUMAN)
                await self.event_publisher.publish(
                    conversation_id, EventType.APPROVAL_REQUESTED,
                    {"run_id": str(run_id), "conversation_id": str(conversation_id),
                     "customer_id": customer_id, "case_id": case_id, "approval_id": approval_id},
                    run_id=run_id, customer_id=customer_id,
                )
                await self.event_publisher.publish(
                    conversation_id, EventType.WORKFLOW_INTERRUPTED,
                    {"run_id": str(run_id), "conversation_id": str(conversation_id),
                     "customer_id": customer_id, "case_id": case_id, "approval_id": approval_id},
                    run_id=run_id, customer_id=customer_id,
                )
                return

            final_response = result.get("final_response", "")
            await self._persist_final_response(run_id, conversation_id, customer_id, final_response)
            await self.agent_run_repo.update_status(run_id, RunStatus.COMPLETED)
            await self.event_publisher.publish(
                conversation_id,
                EventType.CHAT_COMPLETED,
                {"run_id": str(run_id), "conversation_id": str(conversation_id),
                 "customer_id": customer_id, "response": final_response},
                run_id=run_id, customer_id=customer_id,
            )

        except Exception as e:
            logger.error(f"Graph resume {run_id} failed: {e}")
            await self.agent_run_repo.update_status(run_id, RunStatus.FAILED, error_message=str(e))
            await self.event_publisher.publish(
                conversation_id, EventType.CHAT_FAILED,
                {"run_id": str(run_id), "conversation_id": str(conversation_id),
                 "customer_id": customer_id, "error": str(e)},
                run_id=run_id, customer_id=customer_id,
            )

    async def _persist_final_response(
        self, run_id: UUID, conversation_id: UUID, customer_id: str, content: str
    ) -> None:
        from uuid import uuid4

        from app.domain.conversation.entities import Message

        if await self.conversation_repo.has_assistant_message_for_run(conversation_id, run_id):
            return
        await self.conversation_repo.add_message(
            Message(
                message_id=uuid4(), conversation_id=conversation_id, role="assistant",
                content=content, metadata={"run_id": str(run_id)},
            )
        )
        messages = await self.conversation_repo.get_messages(conversation_id)
        await self.memory_service.maybe_summarize(
            conversation_id, customer_id, messages, self.summary_threshold
        )
