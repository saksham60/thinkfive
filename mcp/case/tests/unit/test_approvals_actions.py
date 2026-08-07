from __future__ import annotations

from datetime import timedelta

import pytest

from case.app.errors import CaseMcpError
from case.app.models.domain import Approval, ApprovalStatus, CardState, CardStatus, now


async def request(container, case_id: str, action: str = "FREEZE_CARD", card_id: str = "card_demo_001", actor: str = "agent"):
    return await container.approval.request(case_id, action, {"card_id": card_id}, actor, f"{case_id}:{action}:{card_id}")


async def test_request_is_pending_idempotent_and_moves_case(container, basic_case):
    one = await request(container, basic_case.case_id)
    two = await request(container, basic_case.case_id)
    assert one.approval_id == two.approval_id
    assert one.status == "PENDING"
    assert (await container.cases.get(basic_case.case_id)).status == "AWAITING_APPROVAL"


async def test_request_rejects_wrong_customer_card(container, basic_case):
    with pytest.raises(CaseMcpError) as error:
        await request(container, basic_case.case_id, card_id="card_other")
    assert error.value.code == "CARD_CUSTOMER_MISMATCH"


async def test_approve_records_human_and_executes_stored_action(container, basic_case):
    approval = await request(container, basic_case.case_id)
    result = await container.approval.approve(approval.approval_id, "human_a", "confirmed")
    assert result.status == "APPROVED"
    assert result.reviewed_by == "human_a"
    assert result.executed_at is not None
    assert (await container.cards.get("card_demo_001")).status == "FROZEN"


async def test_self_approval_is_rejected(container, basic_case):
    approval = await request(container, basic_case.case_id, actor="same_actor")
    with pytest.raises(CaseMcpError) as error:
        await container.approval.approve(approval.approval_id, "same_actor")
    assert error.value.code == "SELF_APPROVAL_FORBIDDEN"


async def test_reject_does_not_execute(container, basic_case):
    approval = await request(container, basic_case.case_id)
    rejected = await container.approval.reject(approval.approval_id, "human_a", "insufficient evidence")
    assert rejected.status == "REJECTED"
    assert (await container.cards.get("card_demo_001")).status == "ACTIVE"
    assert (await container.cases.get(basic_case.case_id)).status == "INVESTIGATING"


async def test_already_reviewed_is_rejected(container, basic_case):
    approval = await request(container, basic_case.case_id)
    await container.approval.reject(approval.approval_id, "human_a")
    with pytest.raises(CaseMcpError) as error:
        await container.approval.approve(approval.approval_id, "human_b")
    assert error.value.code == "APPROVAL_ALREADY_REVIEWED"


async def test_expired_approval_is_audited(container, basic_case):
    approval = Approval(
        case_id=basic_case.case_id,
        action_type="FREEZE_CARD",
        action_payload={"card_id": "card_demo_001"},
        requested_by="agent",
        expires_at=now() - timedelta(seconds=1),
    )
    await container.approvals.create(approval)
    with pytest.raises(CaseMcpError) as error:
        await container.approval.approve(approval.approval_id, "human")
    assert error.value.code == "APPROVAL_EXPIRED"
    assert "APPROVAL_EXPIRED" in [x.event_type for x in await container.audits.list(basic_case.case_id, 200)]


async def test_freeze_requires_approval(container, basic_case):
    with pytest.raises(CaseMcpError) as error:
        await container.actions.execute(basic_case.case_id, "missing", "card_demo_001", "FREEZE_CARD")
    assert error.value.code == "APPROVAL_REQUIRED"


async def test_rejected_approval_cannot_execute(container, basic_case):
    approval = await request(container, basic_case.case_id)
    await container.approval.reject(approval.approval_id, "human")
    with pytest.raises(CaseMcpError) as error:
        await container.actions.execute(basic_case.case_id, approval.approval_id, "card_demo_001", "FREEZE_CARD")
    assert error.value.code == "APPROVAL_REQUIRED"


async def test_action_and_case_mismatch_are_rejected(container, basic_case):
    approval = await request(container, basic_case.case_id)
    approved = approval.model_copy(update={"status": ApprovalStatus.APPROVED})
    await container.approvals.update(approved)
    with pytest.raises(CaseMcpError) as action_error:
        await container.actions.execute(basic_case.case_id, approval.approval_id, "card_demo_001", "BLOCK_CARD")
    assert action_error.value.code == "APPROVAL_ACTION_MISMATCH"
    other = await container.case.create("demo_customer_001", "CARD_ISSUE")
    with pytest.raises(CaseMcpError) as case_error:
        await container.actions.execute(other.case_id, approval.approval_id, "card_demo_001", "FREEZE_CARD")
    assert case_error.value.code == "APPROVAL_ACTION_MISMATCH"


async def test_card_transition_matrix_and_blocked_terminal(container):
    case = await container.case.create("demo_customer_001", "CARD_ISSUE")
    freeze = await request(container, case.case_id, "FREEZE_CARD")
    await container.approval.approve(freeze.approval_id, "human")
    assert (await container.cards.get("card_demo_001")).status == "FROZEN"
    await container.case.update(case.case_id, status="INVESTIGATING")
    unfreeze = await request(container, case.case_id, "UNFREEZE_CARD")
    await container.approval.approve(unfreeze.approval_id, "human")
    assert (await container.cards.get("card_demo_001")).status == "ACTIVE"
    await container.case.update(case.case_id, status="INVESTIGATING")
    block = await request(container, case.case_id, "BLOCK_CARD")
    await container.approval.approve(block.approval_id, "human")
    assert (await container.cards.get("card_demo_001")).status == "BLOCKED"
    await container.case.update(case.case_id, status="INVESTIGATING")
    unfreeze_blocked = await request(container, case.case_id, "UNFREEZE_CARD")
    with pytest.raises(CaseMcpError) as error:
        await container.approval.approve(unfreeze_blocked.approval_id, "human2")
    assert error.value.code == "INVALID_CARD_TRANSITION"


async def test_frozen_can_be_blocked(container, basic_case):
    await container.cards.upsert(CardState(card_id="card_demo_001", customer_id="demo_customer_001", status=CardStatus.FROZEN))
    approval = await request(container, basic_case.case_id, "BLOCK_CARD")
    await container.approval.approve(approval.approval_id, "human")
    assert (await container.cards.get("card_demo_001")).status == "BLOCKED"


async def test_duplicate_execution_is_idempotent_but_consumed_cannot_be_reused(container, basic_case):
    approval = await request(container, basic_case.case_id)
    await container.approval.approve(approval.approval_id, "human")
    first = await container.actions.execute(basic_case.case_id, approval.approval_id, "card_demo_001", "FREEZE_CARD")
    second = await container.actions.execute(basic_case.case_id, approval.approval_id, "card_demo_001", "FREEZE_CARD")
    assert first.updated_at == second.updated_at
    await container.cards.upsert(CardState(card_id="card_demo_001", customer_id="demo_customer_001", status=CardStatus.ACTIVE))
    with pytest.raises(CaseMcpError) as error:
        await container.actions.execute(basic_case.case_id, approval.approval_id, "card_demo_001", "FREEZE_CARD")
    assert error.value.code == "APPROVAL_ALREADY_CONSUMED"


async def test_card_state_is_explicitly_synthetic(container):
    card = await container.cards.get("card_demo_001")
    assert card.metadata == {"synthetic": True, "source": "demo_bank_control"}
