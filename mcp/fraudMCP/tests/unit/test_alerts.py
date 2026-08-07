from __future__ import annotations

import pytest

from fraudMCP.app.errors import AlertStateTransitionError, DuplicateAlertError, InvalidInputError


@pytest.mark.asyncio()
async def test_qualifying_assessment_creates_alert(fraud_service, alert_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious")
    alert = await alert_service.create_fraud_alert(assessment.assessment_id)
    assert alert.assessment_id == assessment.assessment_id
    assert alert.customer_id == assessment.customer_id
    assert alert.status.value == "OPEN"


@pytest.mark.asyncio()
async def test_low_risk_assessment_rejected(alert_service, fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_001")
    if assessment.risk_score < 0.65:
        with pytest.raises(InvalidInputError) as exc:
            await alert_service.create_fraud_alert(assessment.assessment_id)
        assert exc.value.code == "ASSESSMENT_BELOW_ALERT_THRESHOLD"


@pytest.mark.asyncio()
async def test_duplicate_alert_prevented(alert_service, fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious")
    await alert_service.create_fraud_alert(assessment.assessment_id)
    with pytest.raises(DuplicateAlertError):
        await alert_service.create_fraud_alert(assessment.assessment_id)


@pytest.mark.asyncio()
async def test_alert_lookup_filters_limit_and_evidence(alert_service, fraud_service) -> None:
    suspicious = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious")
    alert = await alert_service.create_fraud_alert(suspicious.assessment_id)

    by_id = await alert_service.get_fraud_alert(alert.alert_id)
    assert by_id.alert_id == alert.alert_id
    assert by_id.evidence

    listed = await alert_service.get_fraud_alerts(customer_id="demo_customer_001", status="OPEN", severity=suspicious.severity.value, limit=10)
    assert any(item.alert_id == alert.alert_id for item in listed)

    limited = await alert_service.get_fraud_alerts(customer_id="demo_customer_001", limit=1)
    assert len(limited) <= 1


@pytest.mark.asyncio()
async def test_alert_status_transitions(alert_service, fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious")
    alert = await alert_service.create_fraud_alert(assessment.assessment_id)

    investigating = await alert_service.update_fraud_alert_status(alert.alert_id, "INVESTIGATING", note="analyst started")
    assert investigating.status.value == "INVESTIGATING"

    escalated = await alert_service.update_fraud_alert_status(alert.alert_id, "ESCALATED")
    assert escalated.status.value == "ESCALATED"

    resolved = await alert_service.update_fraud_alert_status(alert.alert_id, "RESOLVED")
    assert resolved.status.value == "RESOLVED"


@pytest.mark.asyncio()
async def test_invalid_alert_status_transition(alert_service, fraud_service) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious")
    alert = await alert_service.create_fraud_alert(assessment.assessment_id)
    with pytest.raises(AlertStateTransitionError):
        await alert_service.update_fraud_alert_status(alert.alert_id, "RESOLVED")
