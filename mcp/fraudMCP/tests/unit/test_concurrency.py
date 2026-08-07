from __future__ import annotations

import asyncio

import pytest

from fraudMCP.app.errors import DuplicateAlertError


@pytest.mark.asyncio()
async def test_simultaneous_assessment_same_transaction(fraud_service, container) -> None:
    tasks = [fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious") for _ in range(5)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 5
    assert len({item.assessment_id for item in results}) == 5

    listed = await container.assessments.list_customer_assessments("demo_customer_001", limit=20)
    assert len(listed) >= 5


@pytest.mark.asyncio()
async def test_simultaneous_alert_creation_duplicate_race(fraud_service, alert_service, container) -> None:
    assessment = await fraud_service.assess_transaction_risk("demo_customer_001", "tx_suspicious")

    async def create_once() -> str:
        try:
            alert = await alert_service.create_fraud_alert(assessment.assessment_id)
            return alert.alert_id
        except DuplicateAlertError:
            return "duplicate"

    results = await asyncio.gather(*[create_once() for _ in range(5)])
    success = [item for item in results if item != "duplicate"]
    assert len(success) == 1

    alerts = await container.alerts.list_alerts(customer_id="demo_customer_001", limit=10)
    assert len([item for item in alerts if item.transaction_id == assessment.transaction_id]) == 1


@pytest.mark.asyncio()
async def test_multiple_customers_assessed_simultaneously(fraud_service) -> None:
    c1 = fraud_service.assess_transaction_risk("demo_customer_001", "tx_005")
    c2 = fraud_service.assess_transaction_risk("demo_customer_002", "tx2_001")
    results = await asyncio.gather(c1, c2)
    assert {item.customer_id for item in results} == {"demo_customer_001", "demo_customer_002"}
