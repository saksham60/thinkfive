from __future__ import annotations

import pytest

from fraudMCP.app.errors import (
    BankingProviderCustomerNotFoundError,
    BankingProviderTimeoutError,
    BankingProviderTransactionNotFoundError,
    BankingProviderUnavailableError,
)


@pytest.mark.asyncio()
async def test_assess_transaction_risk_happy_path(fraud_service, fake_banking_provider, container) -> None:
    assessment = await fraud_service.assess_transaction_risk(
        "demo_customer_001",
        "tx_suspicious",
        device_id="device_primary",
        ip_address="203.0.113.50",
        channel="mobile_app",
    )

    assert assessment.customer_id == "demo_customer_001"
    assert assessment.transaction_id == "tx_suspicious"
    assert 0.0 <= assessment.risk_score <= 1.0
    assert assessment.severity.value in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert assessment.scorer_version == "1.0.0"
    assert assessment.feature_schema_version == 1
    assert any(call[0] == "get_transaction" for call in fake_banking_provider.calls)
    assert any(call[0] == "list_recent_transactions" for call in fake_banking_provider.calls)
    assert any(call[0] == "get_account_summary" for call in fake_banking_provider.calls)

    saved = await container.assessments.get_assessment(assessment.assessment_id)
    assert saved.assessment_id == assessment.assessment_id


@pytest.mark.asyncio()
async def test_assessment_does_not_auto_create_alert(fraud_service, container) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_005")
    alerts = await container.alerts.list_alerts(customer_id="demo_customer_001", limit=100)
    assert assessment.assessment_id
    assert alerts == ()


@pytest.mark.asyncio()
async def test_unknown_customer_and_transaction_not_found(fraud_service, fake_banking_provider) -> None:
    fake_banking_provider.set_fail_mode("customer_not_found")
    with pytest.raises(BankingProviderCustomerNotFoundError):
        await fraud_service.assess_transaction_risk("missing_customer", "tx_001")

    fake_banking_provider.set_fail_mode(None)
    with pytest.raises(BankingProviderTransactionNotFoundError):
        await fraud_service.assess_transaction_risk("demo_customer_001", "unknown_tx")


@pytest.mark.asyncio()
async def test_banking_provider_timeout_and_unavailable_not_treated_as_fraud(fraud_service, fake_banking_provider, container) -> None:
    fake_banking_provider.set_fail_mode("timeout")
    with pytest.raises(BankingProviderTimeoutError):
        await fraud_service.assess_transaction_risk("demo_customer_001", "tx_001")

    fake_banking_provider.set_fail_mode("unavailable")
    with pytest.raises(BankingProviderUnavailableError):
        await fraud_service.assess_transaction_risk("demo_customer_001", "tx_001")

    assessments = await container.assessments.list_customer_assessments("demo_customer_001", limit=100)
    assert all(item.transaction_id != "tx_001" for item in assessments)


@pytest.mark.asyncio()
async def test_incomplete_banking_data_still_assesses(fraud_service, fake_banking_provider) -> None:
    fake_banking_provider._transactions["demo_customer_001"].append(
        {
            "transaction_id": "tx_incomplete",
            "account_id": "acc_checking_001",
            "amount": 31.0,
            "currency": "USD",
            "merchant_name": None,
            "transaction_name": "INCOMPLETE",
            "date": None,
            "datetime": None,
            "category": [],
            "location": None,
        }
    )

    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_incomplete")
    assert assessment.assessment_id
    location_feature = next(item for item in assessment.feature_values if item.feature == "location_anomaly")
    assert location_feature.available is False


@pytest.mark.asyncio()
async def test_assessment_recommended_action_non_binding(fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious")
    assert assessment.recommended_action in {"HUMAN_REVIEW_REQUIRED", "CONSIDER_STEP_UP_VERIFICATION", None}
    assert "freeze" not in (assessment.recommended_action or "").lower()
