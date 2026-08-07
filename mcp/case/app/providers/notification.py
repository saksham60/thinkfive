from __future__ import annotations

from typing import Protocol

from case.app.models.domain import Notification
from case.app.repositories.interfaces import NotificationRepository


class NotificationProvider(Protocol):
    """Delivery boundary. Phase 3 implements this as a persistent outbox."""

    async def find_idempotent(self, key: str) -> Notification | None: ...

    async def queue(self, value: Notification) -> Notification: ...


class SupabaseNotificationProvider:
    """Queue notifications through the configured persistent repository.

    This provider never claims external delivery. A future provider can consume
    or replace the outbox without changing MCP tool contracts.
    """

    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    async def find_idempotent(self, key: str) -> Notification | None:
        return await self.repository.find_idempotent(key)

    async def queue(self, value: Notification) -> Notification:
        return await self.repository.create(value)
