from __future__ import annotations

import asyncio

import pytest

from case.app.errors import CaseMcpError


async def test_create_customer_query_and_get(container):
    case = await container.case.create("demo_customer_001", "CUSTOMER_QUERY", title="Question")
    result = await container.case.get(case.case_id)
    assert result["status"] == "OPEN"
    assert result["customer_id"] == "demo_customer_001"
    assert result["recent_notes"] == []


async def test_create_fraud_case_is_grounded_and_prioritized(container):
    case = await container.case.create("demo_customer_001", "FRAUD_INVESTIGATION", fraud_alert_id="alert_demo_001")
    assert case.priority == "HIGH"
    assert case.transaction_id == "txn_demo_001"
    assert case.assessment_id == "assessment_demo_001"
    assert case.metadata["fraud_risk_score"] == 91


async def test_fraud_alert_customer_isolation(container):
    with pytest.raises(CaseMcpError, match="does not belong") as error:
        await container.case.create("demo_customer_001", "FRAUD_INVESTIGATION", fraud_alert_id="alert_other")
    assert error.value.code == "FRAUD_ALERT_NOT_FOUND"


async def test_create_from_alert_and_idempotency(container):
    first, second = await asyncio.gather(
        container.case.from_alert("alert_demo_001"),
        container.case.from_alert("alert_demo_001"),
    )
    assert first.case_id == second.case_id
    assert len(await container.case.search(fraud_alert_id="alert_demo_001")) == 1


async def test_explicit_idempotency_key(container):
    one = await container.case.create("demo_customer_001", "OTHER", idempotency_key="case-key")
    two = await container.case.create("demo_customer_001", "CARD_ISSUE", idempotency_key="case-key")
    assert one.case_id == two.case_id


async def test_search_is_filtered_and_bounded(container):
    await container.case.create("demo_customer_001", "OTHER", priority="LOW")
    await container.case.create("other", "OTHER", priority="HIGH")
    result = await container.case.search(customer_id="demo_customer_001", limit=999)
    assert len(result) == 1
    assert result[0].customer_id == "demo_customer_001"


async def test_update_assign_and_valid_transitions(container, basic_case):
    assigned = await container.case.assign(basic_case.case_id, "team_a")
    assert assigned.status == "TRIAGED"
    updated = await container.case.update(assigned.case_id, status="INVESTIGATING", priority="HIGH", title="Investigating")
    assert updated.status == "INVESTIGATING"
    assert updated.priority == "HIGH"


async def test_invalid_transition_rejected(container, basic_case):
    with pytest.raises(CaseMcpError) as error:
        await container.case.update(basic_case.case_id, status="CLOSED")
    assert error.value.code == "INVALID_CASE_TRANSITION"


async def test_resolve_close_and_closed_mutation_restriction(container, basic_case):
    resolved = await container.case.resolve(basic_case.case_id, "Answered with verified account information.", "agent_a")
    assert resolved.status == "RESOLVED"
    closed = await container.case.close(basic_case.case_id, "agent_a")
    assert closed.status == "CLOSED"
    with pytest.raises(CaseMcpError) as error:
        await container.case.update(basic_case.case_id, title="changed")
    assert error.value.code == "CASE_ALREADY_CLOSED"


async def test_close_requires_resolution(container, basic_case):
    with pytest.raises(CaseMcpError) as error:
        await container.case.close(basic_case.case_id, "agent_a")
    assert error.value.code == "INVALID_CASE_TRANSITION"


async def test_transaction_ownership_is_validated(container):
    with pytest.raises(ValueError, match="transaction not owned"):
        await container.case.create("other", "TRANSACTION_DISPUTE", transaction_id="txn_demo_001")
