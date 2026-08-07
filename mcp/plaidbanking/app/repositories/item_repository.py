from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass


class ItemNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class ItemRecord:
    customer_id: str
    access_token: str
    item_id: str


class ItemRepository(ABC):
    @abstractmethod
    async def register_item(self, customer_id: str, access_token: str, item_id: str) -> None: ...
    @abstractmethod
    async def get_access_token(self, customer_id: str) -> str: ...
    @abstractmethod
    async def get_item_id(self, customer_id: str) -> str: ...
    @abstractmethod
    async def get_customer_id(self, item_id: str) -> str: ...
    @abstractmethod
    async def exists(self, customer_id: str) -> bool: ...
    @abstractmethod
    async def remove(self, customer_id: str) -> None: ...


class InMemoryItemRepository(ItemRepository):
    def __init__(self) -> None:
        self._items: dict[str, ItemRecord] = {}
        self._customers_by_item: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def register_item(self, customer_id: str, access_token: str, item_id: str) -> None:
        if not customer_id or not access_token or not item_id:
            raise ValueError("customer_id, access_token, and item_id are required")
        async with self._lock:
            old = self._items.get(customer_id)
            if old:
                self._customers_by_item.pop(old.item_id, None)
            owner = self._customers_by_item.get(item_id)
            if owner is not None and owner != customer_id:
                raise ValueError("item is already registered to another customer")
            self._items[customer_id] = ItemRecord(customer_id, access_token, item_id)
            self._customers_by_item[item_id] = customer_id

    async def _get(self, customer_id: str) -> ItemRecord:
        async with self._lock:
            record = self._items.get(customer_id)
        if record is None:
            raise ItemNotFoundError("No banking connection exists for this customer.")
        return record

    async def get_access_token(self, customer_id: str) -> str:
        return (await self._get(customer_id)).access_token

    async def get_item_id(self, customer_id: str) -> str:
        return (await self._get(customer_id)).item_id

    async def get_customer_id(self, item_id: str) -> str:
        async with self._lock:
            customer_id = self._customers_by_item.get(item_id)
        if customer_id is None:
            raise ItemNotFoundError("No customer is registered for this Item.")
        return customer_id

    async def exists(self, customer_id: str) -> bool:
        async with self._lock:
            return customer_id in self._items

    async def remove(self, customer_id: str) -> None:
        async with self._lock:
            record = self._items.pop(customer_id, None)
            if record:
                self._customers_by_item.pop(record.item_id, None)
