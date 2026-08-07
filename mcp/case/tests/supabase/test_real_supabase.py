from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_SUPABASE_INTEGRATION_TESTS", "false").lower() != "true",
    reason="set RUN_SUPABASE_INTEGRATION_TESTS=true after applying the test schema",
)


async def test_real_supabase_repository_round_trip():
    from case.app.config import Settings
    from case.app.container import create_container
    from case.app.database import create_supabase_client
    from case.app.models.domain import CardState

    container = create_container(Settings())
    client = create_supabase_client(Settings())
    case = await container.case.create("case_mcp_integration_customer", "OTHER", idempotency_key="case-mcp-integration-round-trip-v1")
    card_id = f"case_test_{case.case_id}"
    try:
        await container.cards.upsert(CardState(card_id=card_id, customer_id=case.customer_id))
        note = await container.case.note(case.case_id, "Supabase integration note")
        approval = await container.approval.request(case.case_id, "FREEZE_CARD", {"card_id": card_id}, "integration_agent")
        approval = await container.approval.approve(approval.approval_id, "integration_human")
        notification = await container.notification.send(case.case_id, "IN_APP", "Integration update", idempotency_key=f"notify:{case.case_id}")
        loaded = await container.case.get(case.case_id)
        assert loaded["case_id"] == case.case_id
        assert note.case_id == case.case_id
        assert approval.executed_at is not None
        assert notification.status == "QUEUED"
        assert (await container.cards.get(card_id)).status == "FROZEN"
        assert len(await container.case.history(case.case_id)) >= 6
    finally:
        for table in ("audit_events", "notifications", "approvals", "case_notes"):
            client.table(table).delete().eq("case_id", case.case_id).execute()
        client.table("card_states").delete().eq("card_id", card_id).execute()
        client.table("cases").delete().eq("case_id", case.case_id).execute()
