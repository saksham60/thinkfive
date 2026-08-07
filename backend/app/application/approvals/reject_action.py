"""Use case: reject a pending sensitive action (human-only entry point)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from app.hitl.service import HITLService


class RejectActionUseCase:
    """Rejects a pending HITL action. Actor identity from backend session only."""

    def __init__(self, hitl_service: HITLService) -> None:
        self.hitl_service = hitl_service

    async def execute(
        self,
        approval_id: str,
        actor_user_id: UUID,
        actor_role: str,
        runtime_context: dict[str, Any],
        note: str | None = None,
    ) -> dict[str, Any]:
        return await self.hitl_service.reject(approval_id, actor_user_id, actor_role, runtime_context, note)
