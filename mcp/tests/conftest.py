from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app import create_app
from case.app.config import Settings as CaseSettings
from config import CombinedSettings
from fraudMCP.app.config import Settings as FraudSettings
from plaidbanking.app.config import Settings as BankingSettings
from plaidbanking.tests.conftest import FakePlaid, transaction


def combined_settings(token: str | None = "combined-test-token") -> CombinedSettings:
    return CombinedSettings(_env_file=None, MCP_PROVIDER_MODE="local", MCP_AUTH_TOKEN=token, LOG_LEVEL="WARNING")


def banking_settings() -> BankingSettings:
    return BankingSettings(
        _env_file=None,
        PLAID_CLIENT_ID="combined-client",
        PLAID_SECRET="combined-secret-value",
        PLAID_ENV="sandbox",
        PLAID_AUTO_BOOTSTRAP=True,
        PLAID_DEFAULT_CUSTOMER_ID="demo_customer_001",
    )


def fraud_settings() -> FraudSettings:
    return FraudSettings(
        _env_file=None,
        MCP_PROVIDER_MODE="local",
        FRAUD_REPOSITORY_BACKEND="memory",
        FRAUD_ENABLE_ISOLATION_FOREST=False,
        FRAUD_ALERT_THRESHOLD=0.20,
        FRAUD_MEDIUM_THRESHOLD=0.20,
        FRAUD_HIGH_THRESHOLD=0.55,
        FRAUD_CRITICAL_THRESHOLD=0.85,
    )


def case_settings() -> CaseSettings:
    return CaseSettings(
        _env_file=None,
        SUPABASE_URL="https://test.invalid",
        SUPABASE_SERVICE_ROLE_KEY="combined-test-service-key",
        MCP_PROVIDER_MODE="local",
        CASE_REPOSITORY_BACKEND="memory",
        CASE_AUTO_SEED=True,
        CASE_ENFORCE_RBAC=True,
    )


def configured_plaid() -> FakePlaid:
    plaid = FakePlaid()
    plaid.accounts_payload = {
        "accounts": [
            {
                "account_id": "account-1",
                "name": "Demo Checking",
                "official_name": "Demo Checking Account",
                "type": "depository",
                "subtype": "checking",
                "mask": "0001",
                "balances": {"available": 1100.0, "current": 1200.0, "iso_currency_code": "USD"},
            }
        ]
    }
    now = datetime.now(UTC)
    history: list[dict[str, Any]] = []
    for index in range(10):
        history.append(
            transaction(
                f"tx-history-{index}",
                customer_id="demo_customer_001",
                amount=20 + index,
                merchant="Local Market",
                date=(now - timedelta(days=index + 1)).date().isoformat(),
                category=("Food and Drink",),
            )
        )
    suspicious = transaction(
        "tx-suspicious",
        customer_id="demo_customer_001",
        amount=2500,
        merchant="New International Electronics",
        date=now.date().isoformat(),
        category=("Electronics",),
    )
    suspicious["location"] = {"city": "Lagos", "region": "LA", "country": "NG"}
    plaid.sync_pages["test-access-token"].append(
        {"added": [*history, suspicious], "modified": [], "removed": [], "next_cursor": "combined-cursor", "has_more": False}
    )
    return plaid


@pytest.fixture
def combined_app():
    return create_app(
        combined_settings=combined_settings(),
        banking_settings=banking_settings(),
        fraud_settings=fraud_settings(),
        case_settings=case_settings(),
        plaid=configured_plaid(),
        force_memory=True,
    )
