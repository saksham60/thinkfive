from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.application.fraud.monitor_transactions import MonitorTransactionsUseCase
from app.application.fraud.process_transaction import ProcessTransactionUseCase


async def test_proactive_monitor_still_processes_unseen_transactions() -> None:
    banking_adapter = SimpleNamespace(
        get_recent_transactions=AsyncMock(
            return_value={"transactions": [{"transaction_id": "new-plaid-id"}]}
        )
    )
    processing_repo = SimpleNamespace(has_baseline=AsyncMock(return_value=True))
    process_transaction = SimpleNamespace(
        execute=AsyncMock(return_value={"assessment": {"assessment_id": "assessment-1"}})
    )

    result = await MonitorTransactionsUseCase(
        banking_adapter, processing_repo, process_transaction
    ).execute("demo_customer_001")

    process_transaction.execute.assert_awaited_once_with(
        "demo_customer_001", "new-plaid-id"
    )
    assert result == {"baseline_established": 0, "assessed": 1}


async def test_event_driven_processing_still_assesses_and_records_real_ids() -> None:
    fraud_adapter = SimpleNamespace(
        assess_transaction_risk=AsyncMock(
            return_value={"assessment_id": "assessment-1", "risk_score": 0.96}
        ),
        create_fraud_alert=AsyncMock(return_value={"alert_id": "alert-1"}),
    )
    processing_repo = SimpleNamespace(
        is_processed=AsyncMock(return_value=False),
        mark_processed=AsyncMock(),
    )
    use_case = ProcessTransactionUseCase(
        fraud_adapter,
        processing_repo,
        SimpleNamespace(publish=AsyncMock()),
    )

    result = await use_case.execute("demo_customer_001", "new-plaid-id")

    fraud_adapter.assess_transaction_risk.assert_awaited_once_with(
        "demo_customer_001", "new-plaid-id"
    )
    fraud_adapter.create_fraud_alert.assert_awaited_once_with(
        assessment_id="assessment-1", customer_id="demo_customer_001"
    )
    processing_repo.mark_processed.assert_awaited_once_with(
        "demo_customer_001",
        "new-plaid-id",
        assessment_id="assessment-1",
        alert_id="alert-1",
    )
    assert result == {
        "assessment": {"assessment_id": "assessment-1", "risk_score": 0.96},
        "alert_id": "alert-1",
    }
