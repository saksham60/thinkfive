"""Use case: retrieve agent execution traces for a run."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from app.infrastructure.repositories.agent_event import AgentEventRepository


class GetTracesUseCase:
    """Retrieves persisted agent_events for a run (agent trace / observability)."""

    def __init__(self, agent_event_repo: AgentEventRepository) -> None:
        self.agent_event_repo = agent_event_repo

    async def execute(self, run_id: UUID) -> list[dict[str, Any]]:
        return await self.agent_event_repo.get_run_events(run_id)
