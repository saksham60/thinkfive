from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Any, cast

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


class SupabaseTransactionRepository(TransactionRepository):
    """Customer-partitioned persistence for the canonical banking store."""

    def __init__(self, client: Any) -> None:
        self.client = client

    async def apply_changes(self, customer_id: str, upserts: list[Transaction], removed_ids: list[str]) -> None:
        if any(tx.customer_id != customer_id for tx in upserts):
            raise ValueError("transaction customer_id does not match repository partition")
        if upserts:
            rows = [self._to_row(tx) for tx in upserts]
            await asyncio.to_thread(
                lambda: self.client.table("banking_transactions").upsert(rows, on_conflict="transaction_id").execute()
            )
        if removed_ids:
            await self.remove_transactions(customer_id, removed_ids)

    async def upsert_transactions(self, customer_id: str, transactions: list[Transaction]) -> None:
        await self.apply_changes(customer_id, transactions, [])

    async def insert_transaction(self, transaction: Transaction) -> Transaction:
        result = await asyncio.to_thread(
            lambda: self.client.table("banking_transactions").insert(self._to_row(transaction)).execute()
        )
        return self._from_row(result.data[0])

    async def remove_transactions(self, customer_id: str, transaction_ids: list[str]) -> None:
        for transaction_id in transaction_ids:
            def run(transaction_id: str = transaction_id) -> Any:
                return (
                    self.client.table("banking_transactions")
                    .delete()
                    .eq("customer_id", customer_id)
                    .eq("transaction_id", transaction_id)
                    .execute()
                )

            await asyncio.to_thread(run)

    async def get_transaction(self, customer_id: str, transaction_id: str) -> Transaction:
        result = await asyncio.to_thread(
            lambda: self.client.table("banking_transactions")
            .select("*")
            .eq("customer_id", customer_id)
            .eq("transaction_id", transaction_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise TransactionNotFoundError("Transaction was not found for this customer.")
        return self._from_row(result.data[0])

    async def search_transactions(self, customer_id: str, filters: TransactionSearchFilters) -> list[Transaction]:
        def run() -> Any:
            query = self.client.table("banking_transactions").select("*").eq("customer_id", customer_id)
            if filters.account_id:
                query = query.eq("account_id", filters.account_id)
            if filters.min_amount is not None:
                query = query.gte("amount", str(filters.min_amount))
            if filters.max_amount is not None:
                query = query.lte("amount", str(filters.max_amount))
            if filters.start_date is not None:
                query = query.gte("transaction_date", filters.start_date.isoformat())
            if filters.end_date is not None:
                query = query.lte("transaction_date", filters.end_date.isoformat())
            if filters.pending is not None:
                query = query.eq("pending", filters.pending)
            return query.order("transaction_date", desc=True).order("created_at", desc=True).order("transaction_id", desc=True).limit(1000).execute()

        result = await asyncio.to_thread(run)
        merchant = filters.merchant.casefold() if filters.merchant else None
        category = filters.category.casefold() if filters.category else None
        transactions = [self._from_row(row) for row in result.data]
        filtered = [
            transaction
            for transaction in transactions
            if (merchant is None or merchant in (transaction.merchant_name or transaction.transaction_name).casefold())
            and (category is None or any(category in value.casefold() for value in transaction.category))
        ]
        return filtered[: filters.limit]

    async def list_recent_transactions(self, customer_id: str, limit: int, account_id: str | None = None) -> list[Transaction]:
        return await self.search_transactions(customer_id, TransactionSearchFilters(account_id=account_id, limit=min(max(limit, 1), 100)))

    async def count(self, customer_id: str) -> int:
        result = await asyncio.to_thread(
            lambda: self.client.table("banking_transactions").select("transaction_id", count="exact").eq("customer_id", customer_id).execute()
        )
        return int(result.count if result.count is not None else len(result.data))

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return None

    @classmethod
    def _from_row(cls, row: dict[str, Any]) -> Transaction:
        raw_metadata = row.get("metadata")
        metadata = cast(dict[str, Any], raw_metadata) if isinstance(raw_metadata, dict) else {}
        category = row.get("category")
        transaction_date = row.get("transaction_date")
        if isinstance(transaction_date, str):
            transaction_date = date.fromisoformat(transaction_date)
        authorized_at = cls._parse_datetime(row.get("authorized_at"))
        posted_at = cls._parse_datetime(row.get("posted_at"))
        return Transaction(
            customer_id=str(row["customer_id"]),
            transaction_id=str(row["transaction_id"]),
            account_id=str(row["account_id"]),
            amount=Decimal(str(row["amount"])),
            currency=row.get("iso_currency_code"),
            merchant_name=row.get("merchant_name"),
            transaction_name=str(row["description"]),
            date=transaction_date,
            authorized_date=authorized_at.date() if authorized_at else None,
            datetime=posted_at or authorized_at,
            pending=bool(row.get("pending", False)),
            category=(str(category),) if category else (),
            personal_finance_category=metadata.get("personal_finance_category"),
            payment_channel=metadata.get("payment_channel"),
            location=metadata.get("location"),
            website=metadata.get("website"),
            logo_url=metadata.get("logo_url"),
            entity_id=metadata.get("entity_id"),
        )

    @staticmethod
    def _to_row(transaction: Transaction) -> dict[str, Any]:
        metadata = {
            key: value
            for key, value in {
                "personal_finance_category": transaction.personal_finance_category,
                "payment_channel": transaction.payment_channel,
                "location": transaction.location,
                "website": transaction.website,
                "logo_url": transaction.logo_url,
                "entity_id": transaction.entity_id,
            }.items()
            if value is not None
        }
        return {
            "transaction_id": transaction.transaction_id,
            "customer_id": transaction.customer_id,
            "account_id": transaction.account_id,
            "amount": str(transaction.amount),
            "merchant_name": transaction.merchant_name,
            "description": transaction.transaction_name,
            "category": transaction.category[0] if transaction.category else None,
            "pending": transaction.pending,
            "transaction_date": transaction.date.isoformat(),
            "authorized_at": transaction.authorized_date.isoformat() if transaction.authorized_date else None,
            "posted_at": transaction.datetime.isoformat() if transaction.datetime else None,
            "iso_currency_code": transaction.currency or "USD",
            "source": "SYNTHETIC",
            "metadata": metadata,
        }
