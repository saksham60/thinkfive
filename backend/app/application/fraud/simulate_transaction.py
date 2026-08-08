"""Simulate a provider-backed transaction, then synchronize and verify it."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.mcp.adapters.banking import BankingMCPAdapter


class SimulateTransactionUseCase:
    """Create a synthetic transaction and verify it through normal Banking MCP reads."""

    _RECENT_LIMIT = 100
    _VERIFICATION_ATTEMPTS = 4
    _RETRY_DELAY_SECONDS = 1.0

    def __init__(
        self,
        banking_adapter: BankingMCPAdapter,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.banking_adapter = banking_adapter
        self.sleep = sleep

    async def execute(self, customer_id: str, amount: float, description: str) -> dict[str, Any]:
        before_response = await self.banking_adapter.get_recent_transactions(
            customer_id, limit=self._RECENT_LIMIT
        )
        before_ids = {
            transaction_id
            for transaction in self._transactions(before_response)
            if (transaction_id := self._transaction_id(transaction)) is not None
        }

        simulation = await self.banking_adapter.simulate_transaction(
            customer_id, amount, description
        )
        result = dict(simulation)

        for attempt in range(self._VERIFICATION_ATTEMPTS):
            await self.banking_adapter.sync_transactions(customer_id)
            after_response = await self.banking_adapter.get_recent_transactions(
                customer_id, limit=self._RECENT_LIMIT
            )
            transaction = self._find_new_transaction(
                self._transactions(after_response), before_ids, amount, description
            )
            if transaction is not None:
                return {**result, "synchronized": True, "transaction": transaction}
            if attempt < self._VERIFICATION_ATTEMPTS - 1:
                await self.sleep(self._RETRY_DELAY_SECONDS)

        return {
            **result,
            "synchronized": False,
            "transaction": None,
            "message": (
                "Transaction was accepted by the banking provider but has not materialized "
                "in the canonical transaction store yet."
            ),
        }

    @classmethod
    def _find_new_transaction(
        cls,
        transactions: list[dict[str, Any]],
        before_ids: set[str],
        amount: float,
        description: str,
    ) -> dict[str, Any] | None:
        for transaction in transactions:
            transaction_id = cls._transaction_id(transaction)
            if transaction_id is None or transaction_id in before_ids:
                continue
            if not cls._amount_matches(transaction.get("amount"), amount):
                continue
            if not cls._description_matches(transaction, description):
                continue
            return transaction
        return None

    @staticmethod
    def _transactions(response: Any) -> list[dict[str, Any]]:
        values: Any = response
        if isinstance(response, dict):
            values = response.get("transactions", response.get("data", []))
            if isinstance(values, dict):
                values = values.get("transactions", [])
        if not isinstance(values, list):
            return []
        return [value for value in values if isinstance(value, dict)]

    @staticmethod
    def _transaction_id(transaction: dict[str, Any]) -> str | None:
        value = transaction.get("transaction_id")
        return str(value) if value else None

    @staticmethod
    def _amount_matches(value: Any, requested: float) -> bool:
        try:
            return Decimal(str(value)) == Decimal(str(requested))
        except (InvalidOperation, TypeError, ValueError):
            return False

    @staticmethod
    def _description_matches(transaction: dict[str, Any], requested: str) -> bool:
        expected = requested.strip().casefold()
        candidates = (
            transaction.get("description"),
            transaction.get("transaction_name"),
            transaction.get("name"),
            transaction.get("merchant_name"),
        )
        return any(str(value).strip().casefold() == expected for value in candidates if value)
