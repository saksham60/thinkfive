from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod


class WebhookEventRepository(ABC):
    @abstractmethod
    async def claim(self, event_id: str, ttl_seconds: int) -> bool: ...


class InMemoryWebhookEventRepository(WebhookEventRepository):
    def __init__(self) -> None:
        self._events: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def claim(self, event_id: str, ttl_seconds: int = 600) -> bool:
        now = time.monotonic()
        async with self._lock:
            self._events = {key: expiry for key, expiry in self._events.items() if expiry > now}
            if event_id in self._events:
                return False
            self._events[event_id] = now + ttl_seconds
            return True
