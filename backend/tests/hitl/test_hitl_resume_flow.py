from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from app.domain.hitl.entities import WorkflowInterrupt
from app.hitl.policy import HITLPolicyEnforcer
from app.hitl.service import HITLService


async def test_approval_executes_case_mcp_action_exactly_once_then_resumes() -> None:
    interrupt = WorkflowInterrupt(
        interrupt_id=uuid4(), run_id=uuid4(), conversation_id=uuid4(), thread_id="thread-1",
        customer_id="trusted-customer", case_id="case-1", approval_id="approval-1",
        interrupt_type="approval", status="WAITING", created_at=datetime.now(UTC),
        resolved_at=None, resolved_by_user_id=None, resume_payload=None, metadata=None,
    )
    coordinator = AsyncMock()
    coordinator.find_waiting_by_approval.return_value = interrupt
    case_adapter = AsyncMock()
    case_adapter.approve_action.return_value = {
        "approval_id": "approval-1", "action_payload": {"card_id": "card-1"}, "executed_at": "now"
    }
    case_adapter.get_card_status.return_value = {"card_id": "card-1", "status": "FROZEN"}
    graph_runner = AsyncMock()
    event_publisher = AsyncMock()
    service = HITLService(
        coordinator, HITLPolicyEnforcer(), case_adapter, AsyncMock(), graph_runner, event_publisher
    )

    result = await service.approve("approval-1", uuid4(), "ANALYST", {"case_agent": object()})

    case_adapter.approve_action.assert_awaited_once()
    case_adapter.freeze_card.assert_not_awaited()
    case_adapter.unfreeze_card.assert_not_awaited()
    case_adapter.block_card.assert_not_awaited()
    coordinator.mark_resolved.assert_awaited_once()
    graph_runner.resume_run.assert_awaited_once()
    assert result["card"]["status"] == "FROZEN"


async def test_rejection_resumes_without_any_card_action() -> None:
    interrupt = WorkflowInterrupt(
        interrupt_id=uuid4(), run_id=uuid4(), conversation_id=uuid4(), thread_id="thread-1",
        customer_id="trusted-customer", case_id="case-1", approval_id="approval-1",
        interrupt_type="approval", status="WAITING", created_at=datetime.now(UTC),
        resolved_at=None, resolved_by_user_id=None, resume_payload=None, metadata=None,
    )
    coordinator = AsyncMock()
    coordinator.find_waiting_by_approval.return_value = interrupt
    case_adapter = AsyncMock()
    case_adapter.reject_action.return_value = {"approval_id": "approval-1", "status": "REJECTED"}
    graph_runner = AsyncMock()
    service = HITLService(
        coordinator, HITLPolicyEnforcer(), case_adapter, AsyncMock(), graph_runner, AsyncMock()
    )

    await service.reject("approval-1", uuid4(), "ANALYST", {}, note="Not authorized")

    case_adapter.reject_action.assert_awaited_once()
    case_adapter.approve_action.assert_not_awaited()
    case_adapter.freeze_card.assert_not_awaited()
    graph_runner.resume_run.assert_awaited_once()
