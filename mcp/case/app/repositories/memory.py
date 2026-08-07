from __future__ import annotations

import asyncio
from typing import Any, Generic, TypeVar

from case.app.errors import fail
from case.app.models.domain import Approval, AuditEvent, CardState, Case, CaseNote, Notification

T = TypeVar("T")


class Locked(Generic[T]):
    def __init__(self) -> None:
        self.data: dict[str, T] = {}
        self.lock = asyncio.Lock()


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self.s = Locked[Case]()

    async def create(self, v: Case) -> Case:
        async with self.s.lock:
            existing = next(
                (
                    x
                    for x in self.s.data.values()
                    if (v.fraud_alert_id and x.fraud_alert_id == v.fraud_alert_id) or (v.idempotency_key and x.idempotency_key == v.idempotency_key)
                ),
                None,
            )
            if existing:
                return existing
            self.s.data[v.case_id] = v
            return v

    async def get(self, i: str) -> Case:
        try:
            return self.s.data[i]
        except KeyError:
            raise fail("CASE_NOT_FOUND", "Case was not found.") from None

    async def update(self, v: Case) -> Case:
        async with self.s.lock:
            self.s.data[v.case_id] = v
            return v

    async def search(self, f: dict[str, Any], limit: int) -> list[Case]:
        values = [v for v in self.s.data.values() if all(x is None or getattr(v, k) == x for k, x in f.items())]
        return sorted(values, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_unique(self, fraud_alert_id: str | None, idempotency_key: str | None) -> Case | None:
        return next(
            (
                x
                for x in self.s.data.values()
                if (fraud_alert_id and x.fraud_alert_id == fraud_alert_id) or (idempotency_key and x.idempotency_key == idempotency_key)
            ),
            None,
        )


class InMemoryCaseNoteRepository:
    def __init__(self) -> None:
        self.s = Locked[CaseNote]()

    async def create(self, v: CaseNote) -> CaseNote:
        self.s.data[v.note_id] = v
        return v

    async def list(self, i: str, limit: int) -> list[CaseNote]:
        return sorted((x for x in self.s.data.values() if x.case_id == i), key=lambda x: x.created_at)[:limit]


class InMemoryApprovalRepository:
    def __init__(self) -> None:
        self.s = Locked[Approval]()

    async def create(self, v: Approval) -> Approval:
        async with self.s.lock:
            old = await self.find_pending(v.case_id, str(v.action_type), v.idempotency_key)
            if old:
                return old
            self.s.data[v.approval_id] = v
            return v

    async def get(self, i: str) -> Approval:
        try:
            return self.s.data[i]
        except KeyError:
            raise fail("APPROVAL_NOT_FOUND", "Approval was not found.") from None

    async def update(self, v: Approval) -> Approval:
        self.s.data[v.approval_id] = v
        return v

    async def list(self, i: str) -> list[Approval]:
        return sorted((x for x in self.s.data.values() if x.case_id == i), key=lambda x: x.requested_at)

    async def find_pending(self, c: str, a: str, k: str | None) -> Approval | None:
        return next(
            (
                x
                for x in self.s.data.values()
                if x.case_id == c and str(x.action_type) == a and str(x.status) == "PENDING" and (not k or x.idempotency_key == k)
            ),
            None,
        )


class InMemoryCardStateRepository:
    def __init__(self) -> None:
        self.s = Locked[CardState]()

    async def get(self, i: str) -> CardState:
        try:
            return self.s.data[i]
        except KeyError:
            raise fail("CARD_NOT_FOUND", "Synthetic card state was not found.") from None

    async def upsert(self, v: CardState) -> CardState:
        self.s.data[v.card_id] = v
        return v


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self.s = Locked[Notification]()

    async def create(self, v: Notification) -> Notification:
        if v.idempotency_key:
            old = await self.find_idempotent(v.idempotency_key)
            if old:
                return old
        self.s.data[v.notification_id] = v
        return v

    async def list(self, i: str) -> list[Notification]:
        return sorted((x for x in self.s.data.values() if x.case_id == i), key=lambda x: x.created_at)

    async def find_idempotent(self, k: str) -> Notification | None:
        return next((x for x in self.s.data.values() if x.idempotency_key == k), None)


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self.s = Locked[AuditEvent]()

    async def append(self, v: AuditEvent) -> AuditEvent:
        self.s.data[v.audit_id] = v
        return v

    async def list(self, i: str, limit: int) -> list[AuditEvent]:
        return sorted((x for x in self.s.data.values() if x.case_id == i), key=lambda x: x.created_at)[:limit]
