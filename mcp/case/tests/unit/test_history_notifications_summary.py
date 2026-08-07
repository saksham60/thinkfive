from __future__ import annotations

import asyncio

import pytest

from case.app.errors import CaseMcpError


async def test_notes_validate_and_order(container, basic_case):
    first = await container.case.note(basic_case.case_id, "first", author_id="agent_a")
    second = await container.case.note(basic_case.case_id, "second", note_type="INVESTIGATION")
    notes = await container.notes.list(basic_case.case_id, 20)
    assert [x.note_id for x in notes] == [first.note_id, second.note_id]
    with pytest.raises(CaseMcpError):
        await container.case.note(basic_case.case_id, "  ")


async def test_note_requires_case(container):
    with pytest.raises(CaseMcpError) as error:
        await container.case.note("missing", "note")
    assert error.value.code == "CASE_NOT_FOUND"


@pytest.mark.parametrize("channel", ["IN_APP", "EMAIL", "SMS"])
async def test_notification_outbox_channels(container, basic_case, channel):
    notification = await container.notification.send(basic_case.case_id, channel, "Grounded update", "Subject")
    assert notification.status == "QUEUED"
    assert notification.provider == "SUPABASE_OUTBOX"
    assert notification.sent_at is None


async def test_notification_validation_and_idempotency(container, basic_case):
    one, two = await asyncio.gather(
        container.notification.send(basic_case.case_id, "SMS", "Update", idempotency_key="notify-key"),
        container.notification.send(basic_case.case_id, "SMS", "Update", idempotency_key="notify-key"),
    )
    assert one.notification_id == two.notification_id
    with pytest.raises(CaseMcpError):
        await container.notification.send(basic_case.case_id, "PAGER", "Update")
    with pytest.raises(CaseMcpError):
        await container.notification.send(basic_case.case_id, "SMS", "x" * 4001)


async def test_notification_requires_case(container):
    with pytest.raises(CaseMcpError) as error:
        await container.notification.send("missing", "IN_APP", "Update")
    assert error.value.code == "CASE_NOT_FOUND"


async def test_grounded_summary_does_not_invent(container, basic_case):
    summary = await container.summary.generate(basic_case.case_id)
    text = summary["human_readable_summary"]
    assert "fraud score" not in text.lower()
    assert "transaction" not in text.lower()
    assert summary["structured_summary"]["approvals"] == []
    assert summary["structured_summary"]["notifications"] == []


async def test_summary_includes_stored_workflow_only(container, basic_case):
    await container.case.note(basic_case.case_id, "Verified customer report")
    await container.notification.send(basic_case.case_id, "IN_APP", "We are reviewing your report")
    approval = await container.approval.request(basic_case.case_id, "FREEZE_CARD", {"card_id": "card_demo_001"}, "agent")
    await container.approval.reject(approval.approval_id, "human")
    summary = await container.summary.generate(basic_case.case_id)
    structured = summary["structured_summary"]
    assert len(structured["notes"]) == 1
    assert structured["approvals"][0]["status"] == "REJECTED"
    assert len(structured["notifications"]) == 1


async def test_audit_history_has_mutations_actor_and_before_after(container, basic_case):
    await container.case.update(basic_case.case_id, title="New title", actor="agent_a")
    await container.case.assign(basic_case.case_id, "team_a")
    await container.case.note(basic_case.case_id, "note", author_id="agent_b")
    await container.notification.send(basic_case.case_id, "IN_APP", "update")
    events = await container.case.history(basic_case.case_id)
    names = [x.event_type for x in events]
    assert names[0] == "CASE_CREATED"
    assert {"CASE_UPDATED", "CASE_ASSIGNED", "CASE_NOTE_ADDED", "NOTIFICATION_CREATED"}.issubset(names)
    updated = next(x for x in events if x.event_type == "CASE_UPDATED" and x.actor_id == "agent_a")
    assert updated.before_state is not None and updated.after_state is not None
    assert events == sorted(events, key=lambda x: x.created_at)


async def test_approved_card_action_is_in_history(container, basic_case):
    approval = await container.approval.request(basic_case.case_id, "FREEZE_CARD", {"card_id": "card_demo_001"}, "agent")
    await container.approval.approve(approval.approval_id, "human")
    events = [x.event_type for x in await container.case.history(basic_case.case_id)]
    assert {"APPROVAL_REQUESTED", "APPROVAL_APPROVED", "CARD_FROZEN", "ACTION_EXECUTED"}.issubset(events)
