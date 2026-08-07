"""In-process SSE event broker (asyncio queues per conversation).

For single-instance/single-worker hackathon deployment. Horizontal scaling
would replace this with a Redis pub/sub backed broker implementing the same
interface - persisted `agent_events` remain the source of truth for replay
regardless of broker implementation.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class InProcessEventBroker:
    """Broadcasts events to subscribed SSE connections via asyncio queues."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, conversation_id: UUID) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        key = str(conversation_id)
        async with self._lock:
            self._subscribers[key].add(queue)
        return queue

    async def unsubscribe(self, conversation_id: UUID, queue: asyncio.Queue[dict[str, Any]]) -> None:
        key = str(conversation_id)
        async with self._lock:
            self._subscribers[key].discard(queue)
            if not self._subscribers[key]:
                del self._subscribers[key]

    async def broadcast(self, conversation_id: UUID, event: dict[str, Any]) -> None:
        key = str(conversation_id)
        async with self._lock:
            queues = list(self._subscribers.get(key, ()))
        for queue in queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"SSE queue full for conversation {conversation_id}, dropping event")
