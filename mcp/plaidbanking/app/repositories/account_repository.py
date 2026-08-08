from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from plaidbanking.app.models.account import Account


class AccountRepository(ABC):
    @abstractmethod
    async def list_accounts(self, customer_id: str) -> list[Account]: ...

    @abstractmethod
    async def get_account(self, customer_id: str, account_id: str) -> Account | None: ...


class SupabaseAccountRepository(AccountRepository):
    def __init__(self, client: Any) -> None:
        self.client = client

    async def list_accounts(self, customer_id: str) -> list[Account]:
        def run() -> Any:
            return (
                self.client.table("banking_accounts")
                .select("*")
                .eq("customer_id", customer_id)
                .eq("status", "ACTIVE")
                .order("account_id")
                .execute()
            )

        result = await asyncio.to_thread(run)
        return [self._map(row) for row in result.data]

    async def get_account(self, customer_id: str, account_id: str) -> Account | None:
        def run() -> Any:
            return (
                self.client.table("banking_accounts")
                .select("*")
                .eq("customer_id", customer_id)
                .eq("account_id", account_id)
                .eq("status", "ACTIVE")
                .limit(1)
                .execute()
            )

        result = await asyncio.to_thread(run)
        return self._map(result.data[0]) if result.data else None

    @staticmethod
    def _map(row: dict[str, Any]) -> Account:
        return Account(
            account_id=str(row["account_id"]),
            name=str(row["name"]),
            official_name=row.get("official_name"),
            type=str(row["account_type"]),
            subtype=row.get("account_subtype"),
            mask=row.get("mask"),
            current_balance=Decimal(str(row["current_balance"])) if row.get("current_balance") is not None else None,
            available_balance=Decimal(str(row["available_balance"])) if row.get("available_balance") is not None else None,
            currency=row.get("iso_currency_code"),
        )
