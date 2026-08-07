from __future__ import annotations

import asyncio

import pytest

from plaidbanking.app.models.transaction import TransactionSearchFilters
from plaidbanking.app.plaid.exceptions import PlaidProviderError
from plaidbanking.tests.conftest import FakePlaid, transaction


@pytest.mark.asyncio
async def test_initial_paginated_sync_and_cursor(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer-1", "token-1", "item-1")
    fake_plaid.sync_pages["token-1"].extend(
        [
            {"added": [transaction("TX1")], "modified": [], "removed": [], "next_cursor": "c1", "has_more": True},
            {"added": [transaction("TX2")], "modified": [], "removed": [], "next_cursor": "c2", "has_more": False},
        ]
    )
    summary = await container.transaction_service.sync("customer-1")
    state = await container.sync_states.get("customer-1")
    assert (summary.added_count, summary.pages_processed, summary.current_repository_count) == (2, 2, 2)
    assert state.cursor == "c2" and not state.stale


@pytest.mark.asyncio
async def test_modified_removed_and_repository_current(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer-1", "token-1", "item-1")
    fake_plaid.sync_pages["token-1"].append(
        {"added": [transaction("TX1"), transaction("TX2")], "modified": [], "removed": [], "next_cursor": "c1", "has_more": False}
    )
    await container.transaction_service.sync("customer-1")
    fake_plaid.sync_pages["token-1"].append(
        {
            "added": [],
            "modified": [transaction("TX2", amount=99)],
            "removed": [{"transaction_id": "TX1"}],
            "next_cursor": "c2",
            "has_more": False,
        }
    )
    summary = await container.transaction_service.sync("customer-1")
    assert (summary.modified_count, summary.removed_count, summary.current_repository_count) == (1, 1, 1)
    assert (await container.transaction_service.get("customer-1", "TX2")).amount == 99


@pytest.mark.asyncio
async def test_cursor_not_committed_on_failure(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer-1", "token-1", "item-1")
    fake_plaid.sync_pages["token-1"].extend(
        [
            {"added": [transaction("TX1")], "modified": [], "removed": [], "next_cursor": "c1", "has_more": True},
            RuntimeError("interrupted"),
        ]
    )
    with pytest.raises(RuntimeError):
        await container.transaction_service.sync("customer-1")
    state = await container.sync_states.get("customer-1")
    assert state.cursor is None and state.stale and state.status == "failed"
    assert await container.transactions.count("customer-1") == 0


@pytest.mark.asyncio
async def test_sync_restarts_after_pagination_mutation(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer-1", "token-1", "item-1")
    fake_plaid.sync_pages["token-1"].extend(
        [
            {"added": [transaction("discarded")], "modified": [], "removed": [], "next_cursor": "c1", "has_more": True},
            PlaidProviderError(
                "Transactions changed during synchronization.",
                error_code="TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION",
            ),
            {"added": [transaction("kept")], "modified": [], "removed": [], "next_cursor": "c2", "has_more": False},
        ]
    )
    summary = await container.transaction_service.sync("customer-1")
    assert summary.current_repository_count == 1
    assert (await container.transactions.get_transaction("customer-1", "kept")).transaction_id == "kept"


@pytest.mark.asyncio
async def test_ensure_sync_only_when_stale(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer-1", "token-1", "item-1")
    await container.transaction_service.recent("customer-1")
    await container.transaction_service.recent("customer-1")
    assert fake_plaid.sync_calls["token-1"] == 1
    await container.sync_states.mark_stale("customer-1")
    await container.transaction_service.search("customer-1", TransactionSearchFilters())
    assert fake_plaid.sync_calls["token-1"] == 2


@pytest.mark.asyncio
async def test_same_customer_sync_is_serialized(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer-1", "token-1", "item-1")
    await asyncio.gather(container.transaction_service.sync("customer-1"), container.transaction_service.sync("customer-1"))
    assert fake_plaid.sync_calls["token-1"] == 2
    assert (await container.sync_states.get("customer-1")).status == "synchronized"


@pytest.mark.asyncio
async def test_different_customers_sync_independently(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("a", "token-a", "item-a")
    await container.items.register_item("b", "token-b", "item-b")
    await asyncio.gather(container.transaction_service.sync("a"), container.transaction_service.sync("b"))
    assert fake_plaid.sync_calls == {"token-a": 1, "token-b": 1}
