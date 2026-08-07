from __future__ import annotations

from typing import Any

import pytest

from case.app.config import Settings
from case.app.container import Container, create_container
from case.app.models.domain import CardState


class FakeBankingProvider:
    async def get_accounts(self, customer_id: str) -> list[dict[str, str]]:
        return [{"customer_id": customer_id, "account_id": "account_demo_001"}]

    async def get_account_summary(self, customer_id: str) -> dict[str, str]:
        return {"customer_id": customer_id}

    async def get_transaction(self, customer_id: str, transaction_id: str) -> dict[str, str]:
        if customer_id != "demo_customer_001" or transaction_id != "txn_demo_001":
            raise ValueError("transaction not owned")
        return {"customer_id": customer_id, "transaction_id": transaction_id}

    async def get_customer_identity(self, customer_id: str) -> dict[str, str]:
        return {"customer_id": customer_id}


class FakeFraudProvider:
    alerts = {
        "alert_demo_001": {
            "alert_id": "alert_demo_001",
            "customer_id": "demo_customer_001",
            "transaction_id": "txn_demo_001",
            "assessment_id": "assessment_demo_001",
            "severity": "HIGH",
            "risk_score": 91,
        },
        "alert_other": {"alert_id": "alert_other", "customer_id": "other", "severity": "LOW"},
    }

    async def get_risk_assessment(self, assessment_id: str) -> dict[str, Any]:
        return {"assessment_id": assessment_id, "risk_score": 91}

    async def get_fraud_alert(self, alert_id: str) -> dict[str, Any]:
        if alert_id not in self.alerts:
            raise ValueError("missing alert")
        return self.alerts[alert_id]

    async def get_fraud_alerts(
        self, customer_id: str | None = None, status: str | None = None, severity: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        return list(self.alerts.values())[:limit]


def test_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-only",
        "CASE_REPOSITORY_BACKEND": "memory",
        "CASE_ENFORCE_RBAC": True,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


async def build_container(**settings: Any) -> Container:
    container = create_container(test_settings(**settings), memory=True, banking=FakeBankingProvider(), fraud=FakeFraudProvider())
    await container.cards.upsert(CardState(card_id="card_demo_001", customer_id="demo_customer_001"))
    await container.cards.upsert(CardState(card_id="card_other", customer_id="other"))
    return container


@pytest.fixture
async def container() -> Container:
    return await build_container()


@pytest.fixture
async def basic_case(container: Container):
    return await container.case.create("demo_customer_001", "CUSTOMER_QUERY", title="Where is my transfer?")


@pytest.fixture
async def fraud_case(container: Container):
    return await container.case.from_alert("alert_demo_001")
