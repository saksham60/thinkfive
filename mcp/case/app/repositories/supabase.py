from __future__ import annotations

import asyncio
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from case.app.errors import CaseMcpError, fail
from case.app.models.domain import Approval, AuditEvent, CardState, Case, CaseNote, Notification

T = TypeVar("T", bound=BaseModel)


class Table(Generic[T]):
    def __init__(self, client: Any, name: str, model: type[T], id_field: str) -> None:
        self.client, self.name, self.model, self.id_field = client, name, model, id_field

    async def insert(self, v: T) -> T:
        try:
            r = await asyncio.to_thread(lambda: self.client.table(self.name).insert(v.model_dump(mode="json")).execute())
        except Exception:
            raise CaseMcpError("DATABASE_UNAVAILABLE", "Case persistence is unavailable.", retryable=True) from None
        return self.model.model_validate(r.data[0])

    async def get(self, i: str, code: str) -> T:
        try:
            r = await asyncio.to_thread(lambda: self.client.table(self.name).select("*").eq(self.id_field, i).limit(1).execute())
        except Exception:
            raise CaseMcpError("DATABASE_UNAVAILABLE", "Case persistence is unavailable.", retryable=True) from None
        if not r.data:
            raise fail(code, f"{self.name.rstrip('s').replace('_', ' ').title()} was not found.")
        return self.model.model_validate(r.data[0])

    async def update(self, v: T) -> T:
        payload = v.model_dump(mode="json", exclude={self.id_field})
        try:
            r = await asyncio.to_thread(lambda: self.client.table(self.name).update(payload).eq(self.id_field, getattr(v, self.id_field)).execute())
        except Exception:
            raise CaseMcpError("DATABASE_UNAVAILABLE", "Case persistence is unavailable.", retryable=True) from None
        return self.model.model_validate(r.data[0])

    async def query(self, filters: dict[str, Any], limit: int, order: str) -> list[T]:
        def run() -> Any:
            q = self.client.table(self.name).select("*")
            for k, v in filters.items():
                if v is not None:
                    q = q.eq(k, v)
            return q.order(order).limit(limit).execute()

        try:
            r = await asyncio.to_thread(run)
        except Exception:
            raise CaseMcpError("DATABASE_UNAVAILABLE", "Case persistence is unavailable.", retryable=True) from None
        return [self.model.model_validate(x) for x in r.data]


class SupabaseCaseRepository:
    def __init__(self, c: Any) -> None:
        self.t = Table(c, "cases", Case, "case_id")

    async def create(self, v: Case) -> Case:
        old = await self.find_unique(v.fraud_alert_id, v.idempotency_key)
        if old:
            return old
        return await self.t.insert(v)

    async def get(self, i: str) -> Case:
        return await self.t.get(i, "CASE_NOT_FOUND")

    async def update(self, v: Case) -> Case:
        return await self.t.update(v)

    async def search(self, f: dict[str, Any], limit: int) -> list[Case]:
        return await self.t.query(f, limit, "created_at")

    async def find_unique(self, fraud_alert_id: str | None, idempotency_key: str | None) -> Case | None:
        if fraud_alert_id:
            x: list[Case] = await self.t.query({"fraud_alert_id": fraud_alert_id}, 1, "created_at")
            if x:
                return x[0]
        if idempotency_key:
            x = await self.t.query({"idempotency_key": idempotency_key}, 1, "created_at")
            if x:
                return x[0]
        return None


class SupabaseCaseNoteRepository:
    def __init__(self, c: Any) -> None:
        self.t = Table(c, "case_notes", CaseNote, "note_id")

    async def create(self, v: CaseNote) -> CaseNote:
        return await self.t.insert(v)

    async def list(self, i: str, limit: int) -> list[CaseNote]:
        return await self.t.query({"case_id": i}, limit, "created_at")


class SupabaseApprovalRepository:
    def __init__(self, c: Any) -> None:
        self.t = Table(c, "approvals", Approval, "approval_id")

    async def create(self, v: Approval) -> Approval:
        old = await self.find_pending(v.case_id, str(v.action_type), v.idempotency_key)
        return old or await self.t.insert(v)

    async def get(self, i: str) -> Approval:
        return await self.t.get(i, "APPROVAL_NOT_FOUND")

    async def update(self, v: Approval) -> Approval:
        return await self.t.update(v)

    async def list(self, i: str) -> list[Approval]:
        return await self.t.query({"case_id": i}, 200, "requested_at")

    async def find_pending(self, c: str, a: str, k: str | None) -> Approval | None:
        f = {"case_id": c, "action_type": a, "status": "PENDING"}
        if k:
            f["idempotency_key"] = k
        x: list[Approval] = await self.t.query(f, 1, "requested_at")
        return x[0] if x else None


class SupabaseCardStateRepository:
    def __init__(self, c: Any) -> None:
        self.c, self.t = c, Table(c, "card_states", CardState, "card_id")

    async def get(self, i: str) -> CardState:
        return await self.t.get(i, "CARD_NOT_FOUND")

    async def upsert(self, v: CardState) -> CardState:
        try:
            r = await asyncio.to_thread(lambda: self.c.table("card_states").upsert(v.model_dump(mode="json")).execute())
        except Exception:
            raise CaseMcpError("DATABASE_UNAVAILABLE", "Card persistence is unavailable.", retryable=True) from None
        return CardState.model_validate(r.data[0])


class SupabaseNotificationRepository:
    def __init__(self, c: Any) -> None:
        self.t = Table(c, "notifications", Notification, "notification_id")

    async def create(self, v: Notification) -> Notification:
        if v.idempotency_key:
            old = await self.find_idempotent(v.idempotency_key)
            if old:
                return old
        return await self.t.insert(v)

    async def list(self, i: str) -> list[Notification]:
        return await self.t.query({"case_id": i}, 200, "created_at")

    async def find_idempotent(self, k: str) -> Notification | None:
        x: list[Notification] = await self.t.query({"idempotency_key": k}, 1, "created_at")
        return x[0] if x else None


class SupabaseAuditRepository:
    def __init__(self, c: Any) -> None:
        self.t = Table(c, "audit_events", AuditEvent, "audit_id")

    async def append(self, v: AuditEvent) -> AuditEvent:
        return await self.t.insert(v)

    async def list(self, i: str, limit: int) -> list[AuditEvent]:
        return await self.t.query({"case_id": i}, limit, "created_at")
