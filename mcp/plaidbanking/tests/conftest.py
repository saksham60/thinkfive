from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

import pytest

from plaidbanking.app.config import Settings
from plaidbanking.app.container import Container, create_container


class FakePlaid:
    def __init__(self) -> None:
        self.sync_pages: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
        self.sync_calls: dict[str, int] = defaultdict(int)
        self.accounts_payload: dict[str, Any] = {"accounts": []}
        self.item_payload: dict[str, Any] = {"item": {"item_id": "item-1", "institution_id": "ins-1", "error": None}}
        self.identity_payload: dict[str, Any] = {"accounts": []}
        self.liabilities_payload: dict[str, Any] = {"liabilities": {}}
        self.webhook_jwk: dict[str, Any] | None = None
        self.created_transactions: list[tuple[str, float, str, str | None]] = []

    async def accounts(self, access_token: str, *, balance: bool = False) -> dict[str, Any]:
        return self.accounts_payload

    async def sync_transactions(self, access_token: str, cursor: str | None) -> dict[str, Any]:
        self.sync_calls[access_token] += 1
        if self.sync_pages[access_token]:
            value = self.sync_pages[access_token].popleft()
            if isinstance(value, Exception):
                raise value
            return value
        return {"added": [], "modified": [], "removed": [], "next_cursor": cursor or "cursor-empty", "has_more": False}

    async def refresh_transactions(self, access_token: str) -> dict[str, Any]:
        return {"request_id": "safe"}

    async def identity(self, access_token: str) -> dict[str, Any]:
        return self.identity_payload

    async def identity_match(self, access_token: str, user: dict[str, Any]) -> dict[str, Any]:
        return {"accounts": [{"account_id": "a1", "legal_name": {"score": 95}}]}

    async def liabilities(self, access_token: str) -> dict[str, Any]:
        return self.liabilities_payload

    async def item(self, access_token: str) -> dict[str, Any]:
        return self.item_payload

    async def create_sandbox_item(self, institution_id: str, webhook: str | None) -> tuple[str, str]:
        return "test-access-token", "item-1"

    async def create_sandbox_transaction(self, access_token: str, amount: float, description: str, transaction_date: str | None) -> dict[str, Any]:
        self.created_transactions.append((access_token, amount, description, transaction_date))
        return {"request_id": "safe"}

    async def fire_sandbox_webhook(self, access_token: str) -> dict[str, Any]:
        return {"request_id": "safe"}

    async def webhook_key(self, key_id: str) -> dict[str, Any]:
        assert self.webhook_jwk is not None
        return {"key": self.webhook_jwk}


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        PLAID_CLIENT_ID="test-client",
        PLAID_SECRET="test-secret",
        PLAID_ENV="sandbox",
        PLAID_AUTO_BOOTSTRAP=False,
    )


@pytest.fixture
def fake_plaid() -> FakePlaid:
    return FakePlaid()


@pytest.fixture
def container(settings: Settings, fake_plaid: FakePlaid) -> Container:
    return create_container(settings, fake_plaid)


def transaction(
    transaction_id: str,
    *,
    customer_id: str = "customer-1",
    account_id: str = "account-1",
    amount: float = 10,
    merchant: str = "Shop",
    date: str = "2026-08-01",
    pending: bool = False,
    category: tuple[str, ...] = ("Shops",),
) -> dict[str, Any]:
    return {
        "customer_id": customer_id,
        "transaction_id": transaction_id,
        "account_id": account_id,
        "amount": amount,
        "merchant_name": merchant,
        "name": merchant,
        "date": date,
        "pending": pending,
        "category": list(category),
        "iso_currency_code": "USD",
    }
