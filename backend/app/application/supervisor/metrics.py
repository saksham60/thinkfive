"""Use case: compute supervisor observability metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.hitl.coordinator import HITLCoordinator
    from app.infrastructure.repositories.agent_event import AgentEventRepository
    from app.infrastructure.repositories.agent_run import AgentRunRepository


class SupervisorMetricsUseCase:
    """Computes real metrics from agent_runs/agent_events - never hardcoded."""

    def __init__(
        self,
        agent_run_repo: AgentRunRepository,
        agent_event_repo: AgentEventRepository,
        hitl_coordinator: HITLCoordinator,
    ) -> None:
        self.agent_run_repo = agent_run_repo
        self.agent_event_repo = agent_event_repo
        self.hitl_coordinator = hitl_coordinator

    async def execute(self) -> dict[str, Any]:
        run_metrics = await self.agent_run_repo.get_metrics()
        event_counts = await self.agent_event_repo.count_by_type()
        waiting = await self.hitl_coordinator.list_waiting()

        return {
            "runs": run_metrics,
            "event_counts": event_counts,
            "waiting_hitl_count": len(waiting),
        }
