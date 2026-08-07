from __future__ import annotations

import pytest

from case.app.errors import CaseMcpError


async def test_banking_fraud_case_approval_flow(combined_app):
    async with combined_app.router.lifespan_context(combined_app):
        banking = combined_app.state.banking
        fraud = combined_app.state.fraud
        case = combined_app.state.case

        accounts = await banking.banking.get_accounts("demo_customer_001", balance=True)
        synced = await banking.transaction_service.sync("demo_customer_001")
        transaction = await banking.transaction_service.get("demo_customer_001", "tx-suspicious")
        assessment = await fraud.fraud_service.assess_transaction_risk("demo_customer_001", transaction.transaction_id)
        alert = await fraud.alert_service.create_fraud_alert(assessment.assessment_id)
        workflow = await case.case.from_alert(alert.alert_id)
        assigned = await case.case.assign(workflow.case_id, "fraud_team_demo")
        note = await case.case.note(workflow.case_id, "Evidence reviewed in combined process.", author_id="agent_demo")
        approval = await case.approval.request(
            workflow.case_id,
            "FREEZE_CARD",
            {"card_id": "card_demo_001"},
            "agent_demo",
            f"freeze:{workflow.case_id}",
        )
        assert (await case.cards.get("card_demo_001")).status == "ACTIVE"
        approved = await case.approval.approve(approval.approval_id, "human_reviewer_demo")
        frozen = await case.actions.execute(workflow.case_id, approval.approval_id, "card_demo_001", "FREEZE_CARD")
        notification = await case.notification.send(workflow.case_id, "IN_APP", "We secured your synthetic demo card.")
        summary = await case.summary.generate(workflow.case_id)
        history = await case.case.history(workflow.case_id)
        resolved = await case.case.resolve(workflow.case_id, "Combined investigation completed.", "human_reviewer_demo")

        assert accounts and synced.added_count == 11
        assert assessment.transaction_id == transaction.transaction_id
        assert alert.assessment_id == assessment.assessment_id
        assert workflow.fraud_alert_id == alert.alert_id
        assert workflow.transaction_id == transaction.transaction_id
        assert assigned.assigned_to == "fraud_team_demo" and note.case_id == workflow.case_id
        assert approved.reviewed_by == "human_reviewer_demo" and approved.executed_at is not None
        assert frozen.status == "FROZEN"
        assert notification.status == "QUEUED" and notification.provider == "SUPABASE_OUTBOX"
        assert summary["structured_summary"]["case"]["fraud_alert_id"] == alert.alert_id
        assert {"APPROVAL_APPROVED", "CARD_FROZEN", "ACTION_EXECUTED"}.issubset({event.event_type for event in history})
        assert resolved.status == "RESOLVED"


async def test_sensitive_action_still_requires_approval(combined_app):
    async with combined_app.router.lifespan_context(combined_app):
        case = combined_app.state.case
        workflow = await case.case.create("demo_customer_001", "CARD_ISSUE")
        with pytest.raises(CaseMcpError) as error:
            await case.actions.execute(workflow.case_id, "arbitrary", "card_demo_001", "FREEZE_CARD")
        assert error.value.code == "APPROVAL_REQUIRED"
        assert (await case.cards.get("card_demo_001")).status == "ACTIVE"
