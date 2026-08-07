from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from plaidbanking.app.models.transaction import Transaction, TransactionSearchFilters
from plaidbanking.app.repositories.transaction_repository import InMemoryTransactionRepository, TransactionNotFoundError


def tx(
    transaction_id: str,
    *,
    customer: str = "a",
    account: str = "one",
    amount: str = "10",
    merchant: str = "Amazon",
    day: int = 1,
    pending: bool = False,
    category: tuple[str, ...] = ("Shopping",),
) -> Transaction:
    return Transaction(
        customer_id=customer,
        transaction_id=transaction_id,
        account_id=account,
        amount=Decimal(amount),
        merchant_name=merchant,
        transaction_name=merchant,
        date=date(2026, 8, day),
        pending=pending,
        category=category,
        currency="USD",
    )


@pytest.mark.asyncio
async def test_added_modified_removed_and_duplicate_upsert() -> None:
    repository = InMemoryTransactionRepository()
    await repository.apply_changes("a", [tx("TX1"), tx("TX2")], [])
    await repository.apply_changes("a", [tx("TX2", amount="25")], [])
    assert (await repository.get_transaction("a", "TX2")).amount == Decimal("25")
    await repository.apply_changes("a", [], ["TX1"])
    assert await repository.count("a") == 1
    with pytest.raises(TransactionNotFoundError):
        await repository.get_transaction("a", "TX1")


@pytest.mark.asyncio
async def test_customer_isolation_and_partition_validation() -> None:
    repository = InMemoryTransactionRepository()
    await repository.upsert_transactions("a", [tx("same", customer="a")])
    await repository.upsert_transactions("b", [tx("same", customer="b", amount="99")])
    assert (await repository.get_transaction("a", "same")).amount == Decimal("10")
    assert (await repository.get_transaction("b", "same")).amount == Decimal("99")
    with pytest.raises(ValueError):
        await repository.upsert_transactions("a", [tx("bad", customer="b")])


@pytest.mark.asyncio
async def test_combined_search_and_ordering() -> None:
    repository = InMemoryTransactionRepository()
    await repository.upsert_transactions(
        "a",
        [
            tx("1", amount="5", day=1),
            tx("2", account="two", amount="50", merchant="Amazon Marketplace", day=2, pending=True),
            tx("3", account="two", amount="75", merchant="Grocery", day=3, category=("Food",)),
        ],
    )
    filters = TransactionSearchFilters(
        account_id="two",
        merchant="amazon",
        min_amount=Decimal("40"),
        max_amount=Decimal("60"),
        start_date=date(2026, 8, 2),
        end_date=date(2026, 8, 2),
        category="shop",
        pending=True,
        limit=10,
    )
    assert [value.transaction_id for value in await repository.search_transactions("a", filters)] == ["2"]
    assert [value.transaction_id for value in await repository.list_recent_transactions("a", 2)] == ["3", "2"]


@pytest.mark.asyncio
async def test_empty_and_limit_enforcement() -> None:
    repository = InMemoryTransactionRepository()
    assert await repository.search_transactions("a", TransactionSearchFilters()) == []
    with pytest.raises(ValueError):
        TransactionSearchFilters(limit=101)
