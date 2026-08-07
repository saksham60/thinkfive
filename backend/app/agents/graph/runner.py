"""LangGraph runner - executes the graph with checkpointing and event publishing."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage
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
        hitl_service: Any,
        max_iterations: int = 15,
    ) -> None:
        self.graph = graph
        self.agent_run_repo = agent_run_repo
        self.agent_event_repo = agent_event_repo
        self.event_publisher = event_publisher
        self.hitl_service = hitl_service
        self.max_iterations = max_iterations

    async def start_run(
        self,
        run_id: UUID,
        conversation_id: UUID,
        thread_id: str,
        customer_id: str,
        message: str,
        runtime_context: dict[str, Any],
    ) -> None:
        """Start a new graph run (called from a background task after chat.accepted)."""
        await self.agent_run_repo.update_status(run_id, RunStatus.RUNNING)
        await self.event_publisher.publish(
            conversation_id, EventType.AGENT_STARTED, {"run_id": str(run_id)}
        )

        config = {
            "configurable": {
                "thread_id": thread_id,
                "customer_id": customer_id,
                "max_iterations": self.max_iterations,
                **runtime_context,
            },
            "recursion_limit": self.max_iterations * 4,
        }

        initial_state = {
            "messages": [HumanMessage(content=message)],
            "conversation_id": str(conversation_id),
            "run_id": str(run_id),
            "thread_id": thread_id,
            "customer_id": customer_id,
            "iteration_count": 0,
            "warnings": [],
            "errors": [],
        }

        try:
            result = await self.graph.ainvoke(initial_state, config=config)

            # Detect interrupt (graph paused waiting for human)
            snapshot = await self.graph.aget_state(config)
            if snapshot.next:
                # Graph paused at hitl_interrupt node
                await self.agent_run_repo.update_status(run_id, RunStatus.WAITING_FOR_HUMAN)
                await self.event_publisher.publish(
                    conversation_id,
                    EventType.WORKFLOW_INTERRUPTED,
                    {"run_id": str(run_id)},
                )
                return

            final_response = result.get("final_response", "")
            await self.agent_run_repo.update_status(run_id, RunStatus.COMPLETED)
            await self.event_publisher.publish(
                conversation_id,
                EventType.CHAT_COMPLETED,
                {"run_id": str(run_id), "response": final_response},
            )

        except Exception as e:
            logger.error(f"Graph run {run_id} failed: {e}")
            await self.agent_run_repo.update_status(run_id, RunStatus.FAILED, error_message=str(e))
            await self.event_publisher.publish(
                conversation_id, EventType.CHAT_FAILED, {"run_id": str(run_id), "error": str(e)}
            )

    async def resume_run(
        self,
        run_id: UUID,
        conversation_id: UUID,
        thread_id: str,
        resume_payload: dict[str, Any],
        runtime_context: dict[str, Any],
    ) -> None:
        """Resume a graph paused at a HITL interrupt using Command(resume=...)."""
        config = {
            "configurable": {
                "thread_id": thread_id,
                **runtime_context,
            },
            "recursion_limit": self.max_iterations * 4,
        }

        await self.agent_run_repo.update_status(run_id, RunStatus.RUNNING)
        await self.event_publisher.publish(
            conversation_id, EventType.WORKFLOW_RESUMED, {"run_id": str(run_id)}
        )

        try:
            result = await self.graph.ainvoke(Command(resume=resume_payload), config=config)

            snapshot = await self.graph.aget_state(config)
            if snapshot.next:
                await self.agent_run_repo.update_status(run_id, RunStatus.WAITING_FOR_HUMAN)
                return

            final_response = result.get("final_response", "")
            await self.agent_run_repo.update_status(run_id, RunStatus.COMPLETED)
            await self.event_publisher.publish(
                conversation_id,
                EventType.CHAT_COMPLETED,
                {"run_id": str(run_id), "response": final_response},
            )

        except Exception as e:
            logger.error(f"Graph resume {run_id} failed: {e}")
            await self.agent_run_repo.update_status(run_id, RunStatus.FAILED, error_message=str(e))
            await self.event_publisher.publish(
                conversation_id, EventType.CHAT_FAILED, {"run_id": str(run_id), "error": str(e)}
            )
