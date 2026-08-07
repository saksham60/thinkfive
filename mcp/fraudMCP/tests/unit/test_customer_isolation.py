from __future__ import annotations

import pytest

from fraudMCP.app.errors import BankingProviderTransactionNotFoundError, CustomerIsolationError


@pytest.mark.asyncio()
async def test_customer_cannot_read_other_assessment(fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_005")
    with pytest.raises(CustomerIsolationError):
        await fraud_service.get_risk_assessment(assessment.assessment_id, customer_id="demo_customer_002")


@pytest.mark.asyncio()
async def test_customer_cannot_access_other_alert(fraud_service, alert_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious")
    alert = await alert_service.create_fraud_alert(assessment.assessment_id)

    with pytest.raises(CustomerIsolationError):
        await alert_service.get_fraud_alert(alert.alert_id, customer_id="demo_customer_002")

    with pytest.raises(CustomerIsolationError):
        await alert_service.update_fraud_alert_status(alert.alert_id, "INVESTIGATING", customer_id="demo_customer_002")


@pytest.mark.asyncio()
async def test_customer_cannot_assess_other_customer_transaction(fraud_service) -> None:
    with pytest.raises(BankingProviderTransactionNotFoundError):
        await fraud_service.assess_transaction_risk("demo_customer_001", "tx2_001")


@pytest.mark.asyncio()
async def test_customer_context_is_isolated(fraud_service) -> None:
    c1 = await fraud_service.get_customer_risk_context("demo_customer_001", history_limit=50)
    c2 = await fraud_service.get_customer_risk_context("demo_customer_002", history_limit=50)
    assert c1["customer_id"] == "demo_customer_001"
    assert c2["customer_id"] == "demo_customer_002"
    assert c1["historical_transaction_count"] != c2["historical_transaction_count"]
