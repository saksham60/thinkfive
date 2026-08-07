from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

from plaidbanking.app.models.transaction import Transaction, TransactionSearchFilters


class TransactionNotFoundError(LookupError):
    pass


class TransactionRepository(ABC):
    @abstractmethod
    async def apply_changes(self, customer_id: str, upserts: list[Transaction], removed_ids: list[str]) -> None: ...
    @abstractmethod
    async def upsert_transactions(self, customer_id: str, transactions: list[Transaction]) -> None: ...
    @abstractmethod
    async def remove_transactions(self, customer_id: str, transaction_ids: list[str]) -> None: ...
    @abstractmethod
    async def get_transaction(self, customer_id: str, transaction_id: str) -> Transaction: ...
    @abstractmethod
    async def search_transactions(self, customer_id: str, filters: TransactionSearchFilters) -> list[Transaction]: ...
    @abstractmethod
    async def list_recent_transactions(self, customer_id: str, limit: int, account_id: str | None = None) -> list[Transaction]: ...
    @abstractmethod
    async def count(self, customer_id: str) -> int: ...


class InMemoryTransactionRepository(TransactionRepository):
    def __init__(self) -> None:
        self._transactions: dict[str, dict[str, Transaction]] = {}
        self._lock = asyncio.Lock()

    async def apply_changes(self, customer_id: str, upserts: list[Transaction], removed_ids: list[str]) -> None:
        if any(tx.customer_id != customer_id for tx in upserts):
            raise ValueError("transaction customer_id does not match repository partition")
        async with self._lock:
            current = dict(self._transactions.get(customer_id, {}))
            for transaction in upserts:
                current[transaction.transaction_id] = transaction
            for transaction_id in removed_ids:
                current.pop(transaction_id, None)
            self._transactions[customer_id] = current

    async def upsert_transactions(self, customer_id: str, transactions: list[Transaction]) -> None:
        await self.apply_changes(customer_id, transactions, [])

    async def remove_transactions(self, customer_id: str, transaction_ids: list[str]) -> None:
        await self.apply_changes(customer_id, [], transaction_ids)

    async def get_transaction(self, customer_id: str, transaction_id: str) -> Transaction:
        async with self._lock:
            transaction = self._transactions.get(customer_id, {}).get(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError("Transaction was not found for this customer.")
        return transaction

    async def search_transactions(self, customer_id: str, filters: TransactionSearchFilters) -> list[Transaction]:
        async with self._lock:
            values = list(self._transactions.get(customer_id, {}).values())
        merchant = filters.merchant.casefold() if filters.merchant else None
        category = filters.category.casefold() if filters.category else None
        result = [
            tx
            for tx in values
            if (filters.account_id is None or tx.account_id == filters.account_id)
            and (merchant is None or merchant in (tx.merchant_name or tx.transaction_name).casefold())
            and (filters.min_amount is None or tx.amount >= filters.min_amount)
            and (filters.max_amount is None or tx.amount <= filters.max_amount)
            and (filters.start_date is None or tx.date >= filters.start_date)
            and (filters.end_date is None or tx.date <= filters.end_date)
            and (category is None or any(category in value.casefold() for value in tx.category))
            and (filters.pending is None or tx.pending == filters.pending)
        ]
        result.sort(key=lambda tx: (tx.datetime.isoformat() if tx.datetime else tx.date.isoformat(), tx.transaction_id), reverse=True)
        return result[: filters.limit]

    async def list_recent_transactions(self, customer_id: str, limit: int, account_id: str | None = None) -> list[Transaction]:
        return await self.search_transactions(customer_id, TransactionSearchFilters(account_id=account_id, limit=min(max(limit, 1), 100)))

    async def count(self, customer_id: str) -> int:
        async with self._lock:
            return len(self._transactions.get(customer_id, {}))
