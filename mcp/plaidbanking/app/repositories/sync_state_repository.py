from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SyncState:
    customer_id: str
    cursor: str | None = None
    last_sync_at: datetime | None = None
    status: str = "never_synchronized"
    stale: bool = True


class SyncStateRepository(ABC):
    @abstractmethod
    async def get(self, customer_id: str) -> SyncState: ...
    @abstractmethod
    async def save(self, state: SyncState) -> None: ...
    @abstractmethod
    async def mark_stale(self, customer_id: str) -> None: ...
    @abstractmethod
    def lock_for(self, customer_id: str) -> asyncio.Lock: ...


class InMemorySyncStateRepository(SyncStateRepository):
    def __init__(self) -> None:
        self._states: dict[str, SyncState] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._index_lock = asyncio.Lock()

    async def get(self, customer_id: str) -> SyncState:
        async with self._index_lock:
            return self._states.get(customer_id, SyncState(customer_id=customer_id))

    async def save(self, state: SyncState) -> None:
        async with self._index_lock:
            self._states[state.customer_id] = state

    async def mark_stale(self, customer_id: str) -> None:
        async with self._index_lock:
            current = self._states.get(customer_id, SyncState(customer_id=customer_id))
            self._states[customer_id] = replace(current, stale=True)

    def lock_for(self, customer_id: str) -> asyncio.Lock:
        # Event-loop execution makes this setdefault atomic between await points.
        return self._locks.setdefault(customer_id, asyncio.Lock())
