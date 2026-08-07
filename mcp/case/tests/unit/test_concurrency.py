from __future__ import annotations

import asyncio

from case.app.errors import CaseMcpError


async def test_concurrent_approval_requests_do_not_duplicate(container, basic_case):
    values = await asyncio.gather(
        *[container.approval.request(basic_case.case_id, "FREEZE_CARD", {"card_id": "card_demo_001"}, "agent", "approval-race") for _ in range(10)]
    )
    assert len({x.approval_id for x in values}) == 1


async def test_concurrent_decisions_have_one_winner(container, basic_case):
    approval = await container.approval.request(basic_case.case_id, "FREEZE_CARD", {"card_id": "card_demo_001"}, "agent")
    results = await asyncio.gather(
        container.approval.approve(approval.approval_id, "human_a"),
        container.approval.reject(approval.approval_id, "human_b"),
        return_exceptions=True,
    )
    assert sum(not isinstance(x, Exception) for x in results) == 1
    assert any(isinstance(x, CaseMcpError) and x.code == "APPROVAL_ALREADY_REVIEWED" for x in results if isinstance(x, Exception))


async def test_concurrent_freeze_retries_are_idempotent(container, basic_case):
    approval = await container.approval.request(basic_case.case_id, "FREEZE_CARD", {"card_id": "card_demo_001"}, "agent")
    await container.approval.approve(approval.approval_id, "human")
    results = await asyncio.gather(*[container.actions.execute(basic_case.case_id, approval.approval_id, "card_demo_001", "FREEZE_CARD") for _ in range(10)])
    assert {x.status for x in results} == {"FROZEN"}
    events = [x.event_type for x in await container.case.history(basic_case.case_id)]
    assert events.count("CARD_FROZEN") == 1
