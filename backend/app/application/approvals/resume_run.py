"""Use case: manually resume a waiting run (used internally by HITLService, exposed for ops)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from app.agents.graph.runner import GraphRunner
    from app.hitl.coordinator import HITLCoordinator


class ResumeRunUseCase:
    """Resumes a specific waiting run given its interrupt_id and a decision payload."""

    def __init__(self, coordinator: HITLCoordinator, graph_runner: GraphRunner) -> None:
        self.coordinator = coordinator
        self.graph_runner = graph_runner

    async def execute(
        self,
        interrupt_id: UUID,
        resume_payload: dict[str, Any],
        runtime_context: dict[str, Any],
    ) -> None:
        interrupt = await self.coordinator.hitl_repo.get_interrupt(interrupt_id)
        if interrupt is None:
            raise ValueError(f"Interrupt {interrupt_id} not found")

        await self.graph_runner.resume_run(
            run_id=interrupt.run_id,
            conversation_id=interrupt.conversation_id,
            thread_id=interrupt.thread_id,
            resume_payload=resume_payload,
            runtime_context=runtime_context,
        )
