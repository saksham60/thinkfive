"""HITL service - top-level orchestration facade used by application use cases.

This is the ONLY place autonomous-vs-human boundary is bridged: it invokes
Case MCP approve_action/reject_action (via CaseMCPAdapter) using the
authenticated human actor context, then resumes the LangGraph thread.
Sensitive tools are never exposed to the autonomous LLM tool registry.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.core.constants import InterruptStatus
from app.hitl.coordinator import HITLCoordinator
from app.hitl.models import ApprovalDecisionPayload
from app.hitl.policy import HITLPolicyEnforcer

if TYPE_CHECKING:
    from app.agents.graph.runner import GraphRunner
    from app.infrastructure.repositories.agent_run import AgentRunRepository
    from app.mcp.adapters.case import CaseMCPAdapter

logger = logging.getLogger(__name__)


class HITLService:
    """Coordinates the full HITL approve/reject/resume flow."""

    def __init__(
        self,
        coordinator: HITLCoordinator,
        policy_enforcer: HITLPolicyEnforcer,
        case_adapter: CaseMCPAdapter,
        agent_run_repo: AgentRunRepository,
        graph_runner: GraphRunner,
    ) -> None:
        self.coordinator = coordinator
        self.policy_enforcer = policy_enforcer
        self.case_adapter = case_adapter
        self.agent_run_repo = agent_run_repo
        self.graph_runner = graph_runner

    async def approve(
        self,
        approval_id: str,
        actor_user_id: UUID,
        actor_role: str,
        runtime_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Approve a pending action: validate role, call Case MCP, resume graph."""
        self.policy_enforcer.assert_can_approve(actor_role)

        interrupt = await self.coordinator.find_waiting_by_approval(approval_id)
        if interrupt is None:
            raise ValueError(f"No waiting workflow found for approval_id={approval_id}")

        # Trusted Case MCP call - actor identity comes from backend auth session,
        # NOT from client-supplied request body fields.
        result = await self.case_adapter.approve_action(
            approval_id=approval_id,
            reviewed_by=str(actor_user_id),
            reviewer_role=actor_role,
        )

        resume_payload = ApprovalDecisionPayload(
            approval_id=approval_id, decision="APPROVED", action_result=result
        ).model_dump()

        await self.coordinator.mark_resolved(
            interrupt.interrupt_id, InterruptStatus.APPROVED, actor_user_id, resume_payload
        )

        await self.graph_runner.resume_run(
            run_id=interrupt.run_id,
            conversation_id=interrupt.conversation_id,
            thread_id=interrupt.thread_id,
            resume_payload=resume_payload,
            runtime_context=runtime_context,
        )

        return result

    async def reject(
        self,
        approval_id: str,
        actor_user_id: UUID,
        actor_role: str,
        runtime_context: dict[str, Any],
        note: str | None = None,
    ) -> dict[str, Any]:
        """Reject a pending action: validate role, call Case MCP, resume graph (no card action)."""
        self.policy_enforcer.assert_can_approve(actor_role)

        interrupt = await self.coordinator.find_waiting_by_approval(approval_id)
        if interrupt is None:
            raise ValueError(f"No waiting workflow found for approval_id={approval_id}")

        result = await self.case_adapter.reject_action(
            approval_id=approval_id,
            reviewed_by=str(actor_user_id),
            reviewer_role=actor_role,
            note=note,
        )

        resume_payload = ApprovalDecisionPayload(
            approval_id=approval_id, decision="REJECTED", action_result=result
        ).model_dump()

        await self.coordinator.mark_resolved(
            interrupt.interrupt_id, InterruptStatus.REJECTED, actor_user_id, resume_payload
        )

        await self.graph_runner.resume_run(
            run_id=interrupt.run_id,
            conversation_id=interrupt.conversation_id,
            thread_id=interrupt.thread_id,
            resume_payload=resume_payload,
            runtime_context=runtime_context,
        )

        return result
