from __future__ import annotations

import pytest

from plaidbanking.app.repositories.item_repository import InMemoryItemRepository, ItemNotFoundError


@pytest.mark.asyncio
async def test_item_lifecycle_and_replace() -> None:
    repository = InMemoryItemRepository()
    await repository.register_item("customer-a", "token-a", "item-a")
    assert await repository.exists("customer-a")
    assert await repository.get_access_token("customer-a") == "token-a"
    assert await repository.get_item_id("customer-a") == "item-a"
    assert await repository.get_customer_id("item-a") == "customer-a"
    await repository.register_item("customer-a", "token-new", "item-new")
    assert await repository.get_access_token("customer-a") == "token-new"
    with pytest.raises(ItemNotFoundError):
        await repository.get_customer_id("item-a")
    await repository.remove("customer-a")
    assert not await repository.exists("customer-a")


@pytest.mark.asyncio
async def test_item_customer_isolation() -> None:
    repository = InMemoryItemRepository()
    await repository.register_item("customer-a", "token-a", "item-a")
    await repository.register_item("customer-b", "token-b", "item-b")
    assert await repository.get_access_token("customer-b") == "token-b"
    with pytest.raises(ValueError):
        await repository.register_item("customer-c", "token-c", "item-a")
    with pytest.raises(ItemNotFoundError):
        await repository.get_access_token("unknown")
