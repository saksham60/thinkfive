from __future__ import annotations

import pytest

from fraudMCP.app.errors import BankingProviderTimeoutError


@pytest.mark.asyncio()
async def test_missing_location_does_not_create_fake_location_evidence(fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_missing_location")
    location_feature = next(item for item in assessment.feature_values if item.feature == "location_anomaly")
    assert location_feature.available is False
    assert location_feature.evidence.get("reason") == "location missing"


@pytest.mark.asyncio()
async def test_missing_device_does_not_auto_flag_unknown_device(fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_005", device_id=None)
    device_feature = next(item for item in assessment.feature_values if item.feature == "device_risk")
    assert device_feature.available is False
    assert device_feature.score is None


@pytest.mark.asyncio()
async def test_provider_timeout_not_converted_to_fraud_evidence(fraud_service, fake_banking_provider, container) -> None:
    fake_banking_provider.set_fail_mode("timeout")
    with pytest.raises(BankingProviderTimeoutError):
        await fraud_service.assess_transaction_risk("demo_customer_001", "tx_001")

    assessments = await container.assessments.list_customer_assessments("demo_customer_001", limit=100)
    assert all(item.transaction_id != "tx_001" for item in assessments)


@pytest.mark.asyncio()
async def test_absent_blacklist_result_not_treated_as_hit(fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_005")
    blacklist_feature = next(item for item in assessment.feature_values if item.feature == "blacklist_risk")
    if blacklist_feature.available:
        assert blacklist_feature.evidence.get("blacklist_hits", 0) >= 0
        assert blacklist_feature.evidence.get("blacklist_hits", 0) == 0


@pytest.mark.asyncio()
async def test_explanation_contains_only_recorded_signals(fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious")
    explanation = await fraud_service.explain_risk(assessment.assessment_id, customer_id="demo_customer_001")

    feature_names = {item.feature for item in assessment.feature_values}
    explained_signal_names = {item["feature"] for item in explanation["signals"]}
    assert explained_signal_names.issubset(feature_names)
    assert "AI thinks" not in explanation["summary"]
