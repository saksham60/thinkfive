from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from plaidbanking.app.config import Settings
from plaidbanking.app.container import create_container
from plaidbanking.app.models.transaction import TransactionSearchFilters
from plaidbanking.app.plaid.exceptions import ResourceNotFoundError


class FakeQuery:
    def __init__(self, tables: dict[str, list[dict[str, Any]]], table: str) -> None:
        self.tables = tables
        self.table = table
        self.filters: list[tuple[str, str, Any]] = []
        self.orders: list[tuple[str, bool]] = []
        self.row_limit: int | None = None
        self.operation = "select"
        self.payload: Any = None
        self.count_requested = False

    def select(self, _columns: str, count: str | None = None) -> FakeQuery:
        self.count_requested = count == "exact"
        return self

    def eq(self, column: str, value: Any) -> FakeQuery:
        self.filters.append((column, "eq", value))
        return self

    def gte(self, column: str, value: Any) -> FakeQuery:
        self.filters.append((column, "gte", value))
        return self

    def lte(self, column: str, value: Any) -> FakeQuery:
        self.filters.append((column, "lte", value))
        return self

    def order(self, column: str, desc: bool = False) -> FakeQuery:
        self.orders.append((column, desc))
        return self

    def limit(self, value: int) -> FakeQuery:
        self.row_limit = value
        return self

    def insert(self, payload: Any) -> FakeQuery:
        self.operation, self.payload = "insert", payload
        return self

    def upsert(self, payload: Any, on_conflict: str | None = None) -> FakeQuery:
        self.operation, self.payload = "upsert", payload
        return self

    def delete(self) -> FakeQuery:
        self.operation = "delete"
        return self

    def execute(self) -> SimpleNamespace:
        if self.operation in {"insert", "upsert"}:
            values = self.payload if isinstance(self.payload, list) else [self.payload]
            for value in values:
                existing = next((row for row in self.tables[self.table] if row.get("transaction_id") == value.get("transaction_id")), None)
                if existing and self.operation == "upsert":
                    existing.update(deepcopy(value))
                elif existing:
                    raise ValueError("duplicate")
                else:
                    row = deepcopy(value)
                    row.setdefault("created_at", datetime.now(UTC).isoformat())
                    self.tables[self.table].append(row)
            return SimpleNamespace(data=deepcopy(values), count=len(values))

        rows = [row for row in self.tables[self.table] if self._matches(row)]
        if self.operation == "delete":
            deleted = deepcopy(rows)
            self.tables[self.table] = [row for row in self.tables[self.table] if not self._matches(row)]
            return SimpleNamespace(data=deleted, count=len(deleted))
        for column, desc in reversed(self.orders):
            rows.sort(key=lambda row, column=column: str(row.get(column) or ""), reverse=desc)
        count = len(rows)
        if self.row_limit is not None:
            rows = rows[: self.row_limit]
        return SimpleNamespace(data=deepcopy(rows), count=count if self.count_requested else None)

    def _matches(self, row: dict[str, Any]) -> bool:
        for column, operation, expected in self.filters:
            actual = row.get(column)
            if operation == "eq" and actual != expected:
                return False
            if operation in {"gte", "lte"}:
                try:
                    left, right = Decimal(str(actual)), Decimal(str(expected))
                except Exception:
                    left, right = str(actual), str(expected)
                if operation == "gte" and left < right:
                    return False
                if operation == "lte" and left > right:
                    return False
        return True


class FakeSupabase:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.tables: dict[str, list[dict[str, Any]]] = {
            "banking_connections": [
                {"customer_id": "demo_customer_001", "provider": "SYNTHETIC", "status": "CONNECTED", "metadata": {}},
                {"customer_id": "other", "provider": "SYNTHETIC", "status": "CONNECTED", "metadata": {}},
            ],
            "banking_accounts": [
                {
                    "account_id": "acct_demo_checking", "customer_id": "demo_customer_001", "name": "Checking",
                    "official_name": "Demo Checking Account", "account_type": "depository", "account_subtype": "checking",
                    "mask": "6620", "current_balance": "500.00", "available_balance": "500.00",
                    "iso_currency_code": "USD", "status": "ACTIVE", "source": "SYNTHETIC",
                },
                {
                    "account_id": "acct_demo_credit", "customer_id": "demo_customer_001", "name": "Credit Card",
                    "official_name": "Demo Credit Card", "account_type": "credit", "account_subtype": "credit card",
                    "mask": "4666", "current_balance": "500.00", "available_balance": "500.00",
                    "iso_currency_code": "USD", "status": "ACTIVE", "source": "SYNTHETIC",
                },
                {
                    "account_id": "acct_other", "customer_id": "other", "name": "Other", "official_name": None,
                    "account_type": "credit", "account_subtype": "credit card", "mask": "9999",
                    "current_balance": "50.00", "available_balance": "50.00", "iso_currency_code": "USD",
                    "status": "ACTIVE", "source": "SYNTHETIC",
                },
            ],
            "banking_transactions": [
                {
                    "transaction_id": "txn_history", "customer_id": "demo_customer_001", "account_id": "acct_demo_checking",
                    "amount": "42.25", "merchant_name": "City Cafe", "description": "Lunch", "category": "Food and Drink",
                    "pending": False, "transaction_date": (now - timedelta(days=1)).date().isoformat(),
                    "authorized_at": None, "posted_at": now.isoformat(), "iso_currency_code": "USD", "source": "SYNTHETIC",
                    "created_at": now.isoformat(), "metadata": {"payment_channel": "in store", "location": {"country": "US"}},
                }
            ],
        }

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self.tables, name)


def settings() -> Settings:
    return Settings(_env_file=None, BANKING_DATA_PROVIDER="supabase", PLAID_AUTO_BOOTSTRAP=True)


async def test_supabase_mode_needs_no_plaid_credentials_and_maps_accounts() -> None:
    client = FakeSupabase()
    container = create_container(settings(), supabase_client=client)

    accounts = await container.banking.get_accounts("demo_customer_001", balance=True)
    summary = await container.banking.get_account_summary("demo_customer_001")

    assert container.plaid is None
    assert container.bootstrap is None
    assert [(account.account_id, account.type, account.subtype) for account in accounts] == [
        ("acct_demo_checking", "depository", "checking"),
        ("acct_demo_credit", "credit", "credit card"),
    ]
    assert all(account.current_balance == Decimal("500.00") for account in accounts)
    assert summary.account_count == 2


async def test_customer_isolation_applies_to_accounts_and_transactions() -> None:
    container = create_container(settings(), supabase_client=FakeSupabase())

    with pytest.raises(ResourceNotFoundError):
        await container.banking.get_account_balance("demo_customer_001", "acct_other")
    with pytest.raises(ResourceNotFoundError, match="Transaction was not found for this customer"):
        await container.transaction_service.get("other", "txn_history")


async def test_transaction_mapping_search_and_noop_sync() -> None:
    container = create_container(settings(), supabase_client=FakeSupabase())

    transaction = await container.transaction_service.get("demo_customer_001", "txn_history")
    search = await container.transaction_service.search(
        "demo_customer_001", TransactionSearchFilters(merchant="cafe", category="food", min_amount=Decimal("40"))
    )
    sync = await container.transaction_service.sync("demo_customer_001")

    assert transaction.amount == Decimal("42.25")
    assert transaction.category == ("Food and Drink",)
    assert transaction.payment_channel == "in store"
    assert search == [transaction]
    assert sync.added_count == 0 and sync.current_repository_count == 1 and sync.pages_processed == 0


async def test_simulation_persists_real_transaction_without_changing_balances() -> None:
    client = FakeSupabase()
    container = create_container(settings(), supabase_client=client)
    balances_before = [(row["account_id"], row["current_balance"], row["available_balance"]) for row in client.tables["banking_accounts"]]

    result = await container.sandbox.simulate_transaction(
        "demo_customer_001", 2500.0, "International Electronics Purchase"
    )
    transaction_id = str(result["transaction"]["transaction_id"])
    persisted = await container.transaction_service.get("demo_customer_001", transaction_id)
    balances_after = [(row["account_id"], row["current_balance"], row["available_balance"]) for row in client.tables["banking_accounts"]]

    assert transaction_id.startswith("txn_")
    assert persisted.account_id == "acct_demo_credit"
    assert persisted.transaction_name == "International Electronics Purchase"
    assert persisted.amount == Decimal("2500.0")
    assert result["transaction"]["source"] == "SYNTHETIC"
    assert balances_after == balances_before


async def test_demo_scenario_persists_only_banking_evidence() -> None:
    client = FakeSupabase()
    container = create_container(settings(), supabase_client=client)

    result = await container.sandbox.create_demo_fraud_scenario("demo_customer_001")

    assert result["scenario_created"] is True
    assert result["transaction"]["description"] == "International Electronics Purchase"
    assert len(client.tables["banking_transactions"]) == 2


async def test_supabase_transaction_is_canonical_fraud_evidence() -> None:
    from fraudMCP.app.config import Settings as FraudSettings
    from fraudMCP.app.container import create_container as create_fraud_container
    from providers import LocalBankingDataProvider

    client = FakeSupabase()
    client.tables["banking_transactions"] = []
    now = datetime.now(UTC)
    merchants = ("Neighborhood Market", "City Cafe", "Metro Transit", "Corner Pharmacy", "Fuel Station")
    categories = ("Groceries", "Food and Drink", "Transportation", "Healthcare", "Fuel")
    for index in range(40):
        client.tables["banking_transactions"].append(
            {
                "transaction_id": f"txn_demo_history_{index:03d}",
                "customer_id": "demo_customer_001",
                "account_id": "acct_demo_checking",
                "amount": str(12 + (index * 13) % 95),
                "merchant_name": merchants[index % len(merchants)],
                "description": f"Normal purchase {index}",
                "category": categories[index % len(categories)],
                "pending": False,
                "transaction_date": (now - timedelta(days=index % 35 + 1)).date().isoformat(),
                "authorized_at": None,
                "posted_at": (now - timedelta(days=index % 35 + 1)).isoformat(),
                "iso_currency_code": "USD",
                "source": "SYNTHETIC",
                "created_at": (now - timedelta(days=index % 35 + 1)).isoformat(),
                "metadata": {"location": {"city": "Austin", "region": "TX", "country": "US"}},
            }
        )
    banking = create_container(settings(), supabase_client=client)
    created = await banking.sandbox.create_demo_fraud_scenario("demo_customer_001")
    transaction_id = str(created["transaction"]["transaction_id"])
    fraud = create_fraud_container(
        FraudSettings(
            _env_file=None,
            MCP_PROVIDER_MODE="local",
            FRAUD_REPOSITORY_BACKEND="memory",
            FRAUD_MIN_MODEL_HISTORY=30,
        ),
        banking_provider=LocalBankingDataProvider(banking),
    )

    assessment = await fraud.fraud_service.assess_transaction_risk("demo_customer_001", transaction_id)
    alert = await fraud.alert_service.create_fraud_alert(assessment.assessment_id)

    assert assessment.transaction_id == transaction_id
    assert assessment.risk_score >= fraud.settings.fraud_alert_threshold
    assert assessment.severity.value in {"HIGH", "CRITICAL"}
    assert alert.transaction_id == transaction_id
    assert alert.alert_id
