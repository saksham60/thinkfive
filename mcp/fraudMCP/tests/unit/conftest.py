from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from fraudMCP.app.config import Settings
from fraudMCP.app.container import Container, create_container
from fraudMCP.app.errors import (
    BankingProviderCustomerNotFoundError,
    BankingProviderTimeoutError,
    BankingProviderTransactionNotFoundError,
    BankingProviderUnavailableError,
)
from fraudMCP.app.providers.banking import BankingDataProvider


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class FakeBankingDataProvider(BankingDataProvider):
    def __init__(self) -> None:
        now = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)
        c1_base = now - timedelta(days=6)

        customer_one_transactions = [
            {
                "transaction_id": "tx_001",
                "account_id": "acc_checking_001",
                "amount": 45.0,
                "currency": "USD",
                "merchant_name": "Neighborhood Market",
                "transaction_name": "NEIGHBORHOOD MARKET",
                "date": _iso(c1_base),
                "datetime": _iso(c1_base),
                "category": ["Food and Drink"],
                "location": {"city": "Boston", "region": "MA", "country": "US"},
            },
            {
                "transaction_id": "tx_002",
                "account_id": "acc_checking_001",
                "amount": 8.5,
                "currency": "USD",
                "merchant_name": "Coffee Box",
                "transaction_name": "COFFEE BOX",
                "date": _iso(c1_base + timedelta(hours=8)),
                "datetime": _iso(c1_base + timedelta(hours=8)),
                "category": ["Food and Drink"],
                "location": {"city": "Boston", "region": "MA", "country": "US"},
            },
            {
                "transaction_id": "tx_003",
                "account_id": "acc_checking_001",
                "amount": 62.0,
                "currency": "USD",
                "merchant_name": "City Utility",
                "transaction_name": "CITY UTILITY",
                "date": _iso(c1_base + timedelta(days=1)),
                "datetime": _iso(c1_base + timedelta(days=1)),
                "category": ["Utilities"],
                "location": {"city": "Boston", "region": "MA", "country": "US"},
            },
            {
                "transaction_id": "tx_004",
                "account_id": "acc_checking_001",
                "amount": 18.0,
                "currency": "USD",
                "merchant_name": "RideNow",
                "transaction_name": "RIDENOW",
                "date": _iso(c1_base + timedelta(days=1, hours=2)),
                "datetime": _iso(c1_base + timedelta(days=1, hours=2)),
                "category": ["Transportation"],
                "location": {"city": "Boston", "region": "MA", "country": "US"},
            },
            {
                "transaction_id": "tx_005",
                "account_id": "acc_checking_001",
                "amount": 74.0,
                "currency": "USD",
                "merchant_name": "Neighborhood Market",
                "transaction_name": "NEIGHBORHOOD MARKET",
                "date": _iso(c1_base + timedelta(days=2)),
                "datetime": _iso(c1_base + timedelta(days=2)),
                "category": ["Food and Drink"],
                "location": {"city": "Boston", "region": "MA", "country": "US"},
            },
            {
                "transaction_id": "tx_006",
                "account_id": "acc_checking_001",
                "amount": 26.0,
                "currency": "USD",
                "merchant_name": "Coffee Box",
                "transaction_name": "COFFEE BOX",
                "date": _iso(c1_base + timedelta(days=2, hours=4)),
                "datetime": _iso(c1_base + timedelta(days=2, hours=4)),
                "category": ["Food and Drink"],
                "location": {"city": "Boston", "region": "MA", "country": "US"},
            },
            {
                "transaction_id": "tx_rapid_1",
                "account_id": "acc_checking_001",
                "amount": 90.0,
                "currency": "USD",
                "merchant_name": "Quick Electronics",
                "transaction_name": "QUICK ELECTRONICS",
                "date": _iso(now - timedelta(hours=2)),
                "datetime": _iso(now - timedelta(hours=2)),
                "category": ["Shops"],
                "location": {"city": "Boston", "region": "MA", "country": "US"},
            },
            {
                "transaction_id": "tx_rapid_2",
                "account_id": "acc_checking_001",
                "amount": 110.0,
                "currency": "USD",
                "merchant_name": "Quick Electronics",
                "transaction_name": "QUICK ELECTRONICS",
                "date": _iso(now - timedelta(hours=1, minutes=15)),
                "datetime": _iso(now - timedelta(hours=1, minutes=15)),
                "category": ["Shops"],
                "location": {"city": "Boston", "region": "MA", "country": "US"},
            },
            {
                "transaction_id": "tx_suspicious",
                "account_id": "acc_checking_001",
                "amount": 2500.0,
                "currency": "USD",
                "merchant_name": "Suspicious Gadgets Outlet",
                "transaction_name": "SUSPICIOUS GADGETS OUTLET",
                "date": _iso(now - timedelta(hours=1)),
                "datetime": _iso(now - timedelta(hours=1)),
                "category": ["Electronics"],
                "location": {"city": "Lagos", "region": "LA", "country": "NG"},
            },
            {
                "transaction_id": "tx_missing_location",
                "account_id": "acc_checking_001",
                "amount": 19.0,
                "currency": "USD",
                "merchant_name": "Small Shop",
                "transaction_name": "SMALL SHOP",
                "date": _iso(now - timedelta(hours=10)),
                "datetime": _iso(now - timedelta(hours=10)),
                "category": ["General Merchandise"],
                "location": None,
            },
        ]

        customer_two_transactions = [
            {
                "transaction_id": "tx2_001",
                "account_id": "acc_checking_002",
                "amount": 20.0,
                "currency": "USD",
                "merchant_name": "Local Deli",
                "transaction_name": "LOCAL DELI",
                "date": _iso(now - timedelta(days=1)),
                "datetime": _iso(now - timedelta(days=1)),
                "category": ["Food and Drink"],
                "location": {"city": "London", "region": "LND", "country": "GB"},
            },
            {
                "transaction_id": "tx2_002",
                "account_id": "acc_checking_002",
                "amount": 23.0,
                "currency": "USD",
                "merchant_name": "Transit GB",
                "transaction_name": "TRANSIT GB",
                "date": _iso(now - timedelta(hours=6)),
                "datetime": _iso(now - timedelta(hours=6)),
                "category": ["Transportation"],
                "location": {"city": "London", "region": "LND", "country": "GB"},
            },
        ]

        self._transactions: dict[str, list[dict[str, Any]]] = {
            "demo_customer_001": customer_one_transactions,
            "demo_customer_002": customer_two_transactions,
        }
        self._accounts: dict[str, list[dict[str, Any]]] = {
            "demo_customer_001": [
                {
                    "account_id": "acc_checking_001",
                    "name": "Primary Checking",
                    "type": "depository",
                    "subtype": "checking",
                    "available_balance": 1200.0,
                    "current_balance": 1234.0,
                    "currency": "USD",
                },
                {
                    "account_id": "acc_credit_001",
                    "name": "Rewards Card",
                    "type": "credit",
                    "subtype": "credit card",
                    "available_balance": 5000.0,
                    "current_balance": 300.0,
                    "currency": "USD",
                },
            ],
            "demo_customer_002": [
                {
                    "account_id": "acc_checking_002",
                    "name": "Customer2 Checking",
                    "type": "depository",
                    "subtype": "checking",
                    "available_balance": 800.0,
                    "current_balance": 810.0,
                    "currency": "USD",
                }
            ],
        }
        self.fail_mode: str | None = None
        self.calls: list[tuple[str, str]] = []

    def set_fail_mode(self, mode: str | None) -> None:
        self.fail_mode = mode

    async def get_transaction(self, customer_id: str, transaction_id: str) -> dict[str, Any]:
        self.calls.append(("get_transaction", customer_id))
        self._maybe_fail(customer_id)
        transactions = self._transactions.get(customer_id)
        if transactions is None:
            raise BankingProviderCustomerNotFoundError("Unknown customer")
        for item in transactions:
            if item["transaction_id"] == transaction_id:
                return dict(item)
        raise BankingProviderTransactionNotFoundError("Unknown transaction for customer")

    async def list_recent_transactions(self, customer_id: str, limit: int = 100, account_id: str | None = None) -> list[dict[str, Any]]:
        self.calls.append(("list_recent_transactions", customer_id))
        self._maybe_fail(customer_id)
        transactions = self._transactions.get(customer_id)
        if transactions is None:
            raise BankingProviderCustomerNotFoundError("Unknown customer")
        items = list(transactions)
        if account_id:
            items = [item for item in items if item.get("account_id") == account_id]
        items.sort(key=lambda item: str(item.get("datetime") or item.get("date")), reverse=True)
        return [dict(item) for item in items[: max(1, min(limit, 100))]]

    async def search_transactions(self, customer_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append(("search_transactions", customer_id))
        self._maybe_fail(customer_id)
        transactions = await self.list_recent_transactions(customer_id, limit=int(filters.get("limit", 100)))

        merchant = filters.get("merchant")
        if isinstance(merchant, str) and merchant.strip():
            needle = merchant.strip().casefold()
            transactions = [item for item in transactions if needle in str(item.get("merchant_name", "")).casefold()]

        category = filters.get("category")
        if isinstance(category, str) and category.strip():
            cat = category.strip().casefold()
            transactions = [
                item for item in transactions if isinstance(item.get("category"), list) and item["category"] and str(item["category"][0]).casefold() == cat
            ]

        min_amount = filters.get("min_amount")
        if min_amount is not None:
            transactions = [item for item in transactions if float(item.get("amount", 0)) >= float(min_amount)]

        max_amount = filters.get("max_amount")
        if max_amount is not None:
            transactions = [item for item in transactions if float(item.get("amount", 0)) <= float(max_amount)]

        return transactions

    async def get_account_summary(self, customer_id: str) -> dict[str, Any]:
        self.calls.append(("get_account_summary", customer_id))
        self._maybe_fail(customer_id)
        accounts = self._accounts.get(customer_id)
        if accounts is None:
            raise BankingProviderCustomerNotFoundError("Unknown customer")

        current_total = sum(float(item.get("current_balance", 0.0)) for item in accounts)
        available_total = sum(float(item.get("available_balance", 0.0)) for item in accounts)
        return {
            "account_count": len(accounts),
            "account_types": {
                "depository": len([a for a in accounts if a.get("type") == "depository"]),
                "credit": len([a for a in accounts if a.get("type") == "credit"]),
            },
            "totals_by_currency": [
                {
                    "currency": "USD",
                    "current_balance": current_total,
                    "available_balance": available_total,
                }
            ],
            "accounts": accounts,
        }

    async def get_accounts(self, customer_id: str) -> list[dict[str, Any]]:
        self.calls.append(("get_accounts", customer_id))
        self._maybe_fail(customer_id)
        accounts = self._accounts.get(customer_id)
        if accounts is None:
            raise BankingProviderCustomerNotFoundError("Unknown customer")
        return [dict(item) for item in accounts]

    def _maybe_fail(self, customer_id: str) -> None:
        if self.fail_mode == "timeout":
            raise BankingProviderTimeoutError("Timed out")
        if self.fail_mode == "unavailable":
            raise BankingProviderUnavailableError("Provider unavailable")
        if self.fail_mode == "customer_not_found":
            raise BankingProviderCustomerNotFoundError("Unknown customer")


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        BANKING_MCP_URL="http://banking.test/mcp",
        MCP_PROVIDER_MODE="local",
        FRAUD_REPOSITORY_BACKEND="memory",
        FRAUD_ENABLE_ISOLATION_FOREST=False,
        FRAUD_MCP_MOUNT_PATH="/mcp",
        FRAUD_HISTORY_LIMIT=100,
        FRAUD_ASSESSMENT_MAX_BATCH=100,
        FRAUD_ALERT_THRESHOLD=0.65,
        FRAUD_MEDIUM_THRESHOLD=0.35,
        FRAUD_HIGH_THRESHOLD=0.65,
        FRAUD_CRITICAL_THRESHOLD=0.85,
    )


@pytest.fixture()
def fake_banking_provider() -> FakeBankingDataProvider:
    return FakeBankingDataProvider()


@pytest.fixture()
def container(settings: Settings, fake_banking_provider: FakeBankingDataProvider) -> Container:
    return create_container(settings, banking_provider=fake_banking_provider)


@pytest.fixture()
def fraud_service(container: Container):
    return container.fraud_service


@pytest.fixture()
def alert_service(container: Container):
    return container.alert_service
