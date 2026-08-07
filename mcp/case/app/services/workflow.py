from __future__ import annotations

import asyncio
from typing import Any, cast

from case.app.authorization import AuthorizationPolicy
from case.app.errors import CaseMcpError, fail
from case.app.models.domain import (
    ALLOWED_CASE_TRANSITIONS,
    CARD_TRANSITIONS,
    ActionType,
    Approval,
    ApprovalStatus,
    AuditEvent,
    CardState,
    CardStatus,
    Case,
    CaseNote,
    CaseStatus,
    CaseType,
    Notification,
    Priority,
    now,
)
from case.app.providers import BankingDataProvider, FraudDataProvider, NotificationProvider
from case.app.repositories.interfaces import (
    ApprovalRepository,
    AuditRepository,
    CardStateRepository,
    CaseNoteRepository,
    CaseRepository,
    NotificationRepository,
)


def dump(v: Any) -> dict[str, Any]:
    return cast(dict[str, Any], v.model_dump(mode="json"))


class AuditService:
    def __init__(self, r: AuditRepository) -> None:
        self.r = r

    async def record(self, event: str, entity: Any, case: Case, actor: str = "SYSTEM", before: Any = None, after: Any = None) -> AuditEvent:
        return await self.r.append(
            AuditEvent(
                case_id=case.case_id,
                customer_id=case.customer_id,
                actor_type="SYSTEM" if actor == "SYSTEM" else "HUMAN",
                actor_id=actor,
                event_type=event,
                entity_type=type(entity).__name__.upper(),
                entity_id=str(
                    getattr(entity, "approval_id", None)
                    or getattr(entity, "card_id", None)
                    or getattr(entity, "notification_id", None)
                    or getattr(entity, "note_id", None)
                    or getattr(entity, "case_id", "")
                ),
                action=event,
                before_state=dump(before) if before else None,
                after_state=dump(after or entity),
            )
        )


class CaseService:
    def __init__(
        self,
        cases: CaseRepository,
        notes: CaseNoteRepository,
        approvals: ApprovalRepository,
        cards: CardStateRepository,
        notifications: NotificationRepository,
        audit: AuditService,
        banking: BankingDataProvider,
        fraud: FraudDataProvider,
    ) -> None:
        self.cases, self.notes, self.approvals, self.cards, self.notifications, self.audit, self.banking, self.fraud = (
            cases,
            notes,
            approvals,
            cards,
            notifications,
            audit,
            banking,
            fraud,
        )
        self.lock = asyncio.Lock()

    async def create(
        self,
        customer_id: str,
        case_type: str,
        title: str | None = None,
        description: str | None = None,
        transaction_id: str | None = None,
        fraud_alert_id: str | None = None,
        assessment_id: str | None = None,
        priority: str | None = None,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Case:
        async with self.lock:
            old = await self.cases.find_unique(fraud_alert_id, idempotency_key)
            if old:
                return old
            data: dict[str, Any] = {}
            if fraud_alert_id:
                data = await self.fraud.get_fraud_alert(fraud_alert_id)
                alert_customer = data.get("customer_id")
                if alert_customer != customer_id:
                    raise fail("FRAUD_ALERT_NOT_FOUND", "Fraud alert does not belong to this customer.")
                transaction_id = transaction_id or data.get("transaction_id")
                assessment_id = assessment_id or data.get("assessment_id")
                priority = priority or str(data.get("severity", "MEDIUM")).upper()
            if transaction_id:
                await self.banking.get_transaction(customer_id, transaction_id)
            value = Case(
                customer_id=customer_id,
                case_type=CaseType(case_type),
                title=title,
                description=description,
                transaction_id=transaction_id,
                fraud_alert_id=fraud_alert_id,
                assessment_id=assessment_id,
                priority=Priority(priority or "MEDIUM"),
                metadata={
                    **(metadata or {}),
                    **(
                        {
                            "fraud_evidence_reference": fraud_alert_id,
                            "fraud_severity": data.get("severity"),
                            "fraud_risk_score": data.get("risk_score"),
                        }
                        if fraud_alert_id
                        else {}
                    ),
                },
                idempotency_key=idempotency_key,
            )
            value = await self.cases.create(value)
            await self.audit.record("CASE_CREATED", value, value)
            return value

    async def from_alert(self, alert_id: str, title: str | None = None, description: str | None = None) -> Case:
        old = await self.cases.find_unique(alert_id, None)
        if old:
            return old
        a = await self.fraud.get_fraud_alert(alert_id)
        return await self.create(a["customer_id"], "FRAUD_INVESTIGATION", title, description, fraud_alert_id=alert_id, idempotency_key=f"fraud:{alert_id}")

    async def get(self, i: str) -> dict[str, Any]:
        c = await self.cases.get(i)
        aps = await self.approvals.list(i)
        notes = await self.notes.list(i, 20)
        action_states: list[dict[str, Any]] = []
        for approval in aps:
            card_id = approval.action_payload.get("card_id")
            if card_id:
                try:
                    card = await self.cards.get(card_id)
                except CaseMcpError as exc:
                    if exc.code == "CARD_NOT_FOUND":
                        continue
                    raise
                action_states.append(dump(card))
        return {
            **dump(c),
            "approval_summary": [dump(x) for x in aps],
            "recent_notes": [dump(x) for x in notes],
            "relevant_action_state": action_states,
        }

    async def status(self, i: str) -> dict[str, Any]:
        c = await self.cases.get(i)
        aps = await self.approvals.list(i)
        return {
            "case_id": i,
            "status": c.status,
            "priority": c.priority,
            "assigned_to": c.assigned_to,
            "pending_approval_count": sum(str(x.status) == "PENDING" for x in aps),
            "last_updated_at": c.updated_at,
            "resolution_status": "resolved" if c.resolution else "unresolved",
        }

    async def search(self, limit: int = 100, **f: Any) -> list[Case]:
        return await self.cases.search(f, min(max(limit, 1), 100))

    async def update(self, i: str, actor: str = "agent", **changes: Any) -> Case:
        before = await self.cases.get(i)
        if str(before.status) == "CLOSED":
            raise fail("CASE_ALREADY_CLOSED", "Closed cases cannot be modified.")
        changes = {k: v for k, v in changes.items() if v is not None}
        if "status" in changes:
            target = str(changes["status"])
            if target not in ALLOWED_CASE_TRANSITIONS[str(before.status)]:
                raise fail("INVALID_CASE_TRANSITION", f"Transition {before.status} to {target} is not allowed.")
            changes["status"] = CaseStatus(target)
        if "priority" in changes:
            changes["priority"] = Priority(changes["priority"])
        if "metadata" in changes:
            changes["metadata"] = {**before.metadata, **changes["metadata"]}
        after = before.model_copy(update={**changes, "updated_at": now()})
        await self.cases.update(after)
        await self.audit.record("CASE_UPDATED", after, after, actor, before, after)
        return after

    async def assign(self, i: str, assignee: str) -> Case:
        c = await self.cases.get(i)
        target = "TRIAGED" if str(c.status) == "OPEN" else None
        result = await self.update(i, assigned_to=assignee, status=target)
        await self.audit.record("CASE_ASSIGNED", result, result, assignee, c, result)
        return result

    async def note(self, i: str, content: str, note_type: str = "GENERAL", author_type: str = "AGENT", author_id: str | None = None) -> CaseNote:
        c = await self.cases.get(i)
        if not content.strip() or len(content) > 8000:
            raise fail("INVALID_INPUT", "Note content must contain 1 to 8000 characters.")
        n = await self.notes.create(CaseNote(case_id=i, content=content.strip(), note_type=note_type, author_type=author_type, author_id=author_id))
        await self.audit.record("CASE_NOTE_ADDED", n, c, author_id or author_type)
        return n

    async def resolve(self, i: str, resolution: str, actor: str) -> Case:
        if not resolution.strip():
            raise fail("INVALID_INPUT", "Resolution is required.")
        c = await self.update(i, status="RESOLVED", resolution=resolution.strip(), resolved_at=now(), actor=actor)
        await self.audit.record("CASE_RESOLVED", c, c, actor)
        return c

    async def close(self, i: str, actor: str) -> Case:
        c = await self.cases.get(i)
        if str(c.status) != "RESOLVED" or not c.resolution:
            raise fail("INVALID_CASE_TRANSITION", "Only resolved cases can be closed.")
        if any(str(x.status) == "PENDING" for x in await self.approvals.list(i)):
            raise fail("PENDING_APPROVAL", "Pending approvals prevent closure.")
        c = await self.update(i, status="CLOSED", closed_at=now(), actor=actor)
        await self.audit.record("CASE_CLOSED", c, c, actor)
        return c

    async def history(self, i: str, limit: int = 200) -> list[AuditEvent]:
        await self.cases.get(i)
        return await self.audit.r.list(i, min(limit, 200))


class ActionService:
    def __init__(self, cases: CaseRepository, approvals: ApprovalRepository, cards: CardStateRepository, audit: AuditService) -> None:
        self.cases, self.approvals, self.cards, self.audit = cases, approvals, cards, audit
        self.locks: dict[str, asyncio.Lock] = {}

    async def execute(self, case_id: str, approval_id: str, card_id: str, action: str, actor: str = "approved_workflow") -> CardState:
        async with self.locks.setdefault(card_id, asyncio.Lock()):
            c = await self.cases.get(case_id)
            try:
                a = await self.approvals.get(approval_id)
            except CaseMcpError as exc:
                if exc.code == "APPROVAL_NOT_FOUND":
                    raise fail("APPROVAL_REQUIRED", "This action requires an approved human authorization.") from None
                raise
            if str(a.status) != "APPROVED":
                raise fail("APPROVAL_REQUIRED", "This action requires an approved human authorization.")
            if a.case_id != case_id or str(a.action_type) != action or a.action_payload.get("card_id") != card_id:
                raise fail("APPROVAL_ACTION_MISMATCH", "Approval does not match this card action.")
            card = await self.cards.get(card_id)
            if card.customer_id != c.customer_id:
                raise fail("CARD_CUSTOMER_MISMATCH", "Card does not belong to the case customer.")
            target = {"FREEZE_CARD": "FROZEN", "UNFREEZE_CARD": "ACTIVE", "BLOCK_CARD": "BLOCKED"}[action]
            if a.executed_at:
                if str(card.status) == target and card.last_case_id == case_id:
                    return card
                raise fail("APPROVAL_ALREADY_CONSUMED", "This approval has already been consumed.")
            if str(card.status) == target:
                if not a.executed_at:
                    await self.approvals.update(a.model_copy(update={"executed_at": now()}))
                return card
            if target not in CARD_TRANSITIONS[str(card.status)]:
                raise fail("INVALID_CARD_TRANSITION", f"Card transition {card.status} to {target} is not allowed.")
            updated = card.model_copy(
                update={"previous_status": card.status, "status": CardStatus(target), "updated_at": now(), "updated_by": actor, "last_case_id": case_id}
            )
            await self.cards.upsert(updated)
            updated_approval = a.model_copy(update={"executed_at": a.executed_at or now()})
            await self.approvals.update(updated_approval)
            await self.audit.record(
                {"FREEZE_CARD": "CARD_FROZEN", "UNFREEZE_CARD": "CARD_UNFROZEN", "BLOCK_CARD": "CARD_BLOCKED"}[action], updated, c, actor, card, updated
            )
            await self.audit.record("ACTION_EXECUTED", updated_approval, c, actor, a, updated_approval)
            return updated


class ApprovalService:
    def __init__(self, cases: CaseRepository, repo: ApprovalRepository, audit: AuditService, actions: ActionService, policy: AuthorizationPolicy) -> None:
        self.cases, self.repo, self.audit, self.actions, self.policy = cases, repo, audit, actions, policy
        self.lock = asyncio.Lock()

    async def request(
        self, case_id: str, action_type: str, payload: dict[str, Any], requested_by: str = "agent", idempotency_key: str | None = None
    ) -> Approval:
        async with self.lock:
            c = await self.cases.get(case_id)
            if str(c.status) in {"CLOSED", "RESOLVED"}:
                raise fail("CASE_ALREADY_CLOSED", "Resolved or closed cases cannot request actions.")
            action = ActionType(action_type)
            if not payload.get("card_id"):
                raise fail("INVALID_INPUT", "action_payload.card_id is required.")
            card = await self.actions.cards.get(payload["card_id"])
            if card.customer_id != c.customer_id:
                raise fail("CARD_CUSTOMER_MISMATCH", "Card does not belong to the case customer.")
            old = await self.repo.find_pending(case_id, str(action), idempotency_key)
            if old:
                return old
            a = await self.repo.create(
                Approval(case_id=case_id, action_type=action, action_payload=payload, requested_by=requested_by, idempotency_key=idempotency_key)
            )
            await self.cases.update(c.model_copy(update={"status": CaseStatus.AWAITING_APPROVAL, "updated_at": now()}))
            await self.audit.record("APPROVAL_REQUESTED", a, c, requested_by)
            return a

    async def approve(self, i: str, reviewed_by: str, note: str | None = None, reviewer_role: str = "HUMAN_REVIEWER") -> Approval:
        async with self.lock:
            a = await self.repo.get(i)
            c = await self.cases.get(a.case_id)
            if str(a.status) != "PENDING":
                raise fail("APPROVAL_ALREADY_REVIEWED", "Approval has already been reviewed.")
            if a.expires_at and a.expires_at < now():
                expired = await self.repo.update(a.model_copy(update={"status": ApprovalStatus.EXPIRED}))
                await self.audit.record("APPROVAL_EXPIRED", expired, c, reviewed_by, a, expired)
                raise fail("APPROVAL_EXPIRED", "Approval has expired.")
            self.policy.can_review(a.requested_by, reviewed_by, reviewer_role)
            card = await self.actions.cards.get(a.action_payload["card_id"])
            target = {"FREEZE_CARD": "FROZEN", "UNFREEZE_CARD": "ACTIVE", "BLOCK_CARD": "BLOCKED"}[str(a.action_type)]
            if str(card.status) != target and target not in CARD_TRANSITIONS[str(card.status)]:
                raise fail("INVALID_CARD_TRANSITION", f"Card transition {card.status} to {target} is not allowed.")
            a = await self.repo.update(
                a.model_copy(update={"status": ApprovalStatus.APPROVED, "reviewed_by": reviewed_by, "reviewed_at": now(), "review_note": note})
            )
            await self.cases.update(c.model_copy(update={"status": CaseStatus.ACTION_APPROVED, "updated_at": now()}))
            await self.audit.record("APPROVAL_APPROVED", a, c, reviewed_by)
            await self.actions.execute(a.case_id, a.approval_id, a.action_payload["card_id"], str(a.action_type), reviewed_by)
            return await self.repo.get(i)

    async def reject(self, i: str, reviewed_by: str, note: str | None = None, reviewer_role: str = "HUMAN_REVIEWER") -> Approval:
        async with self.lock:
            a = await self.repo.get(i)
            c = await self.cases.get(a.case_id)
            if str(a.status) != "PENDING":
                raise fail("APPROVAL_ALREADY_REVIEWED", "Approval has already been reviewed.")
            self.policy.can_review(a.requested_by, reviewed_by, reviewer_role)
            a = await self.repo.update(
                a.model_copy(update={"status": ApprovalStatus.REJECTED, "reviewed_by": reviewed_by, "reviewed_at": now(), "review_note": note})
            )
            await self.cases.update(c.model_copy(update={"status": CaseStatus.INVESTIGATING, "updated_at": now()}))
            await self.audit.record("APPROVAL_REJECTED", a, c, reviewed_by)
            return a


class NotificationService:
    def __init__(self, cases: CaseRepository, provider: NotificationProvider, audit: AuditService) -> None:
        self.cases, self.provider, self.audit = cases, provider, audit
        self.lock = asyncio.Lock()

    async def send(self, case_id: str, channel: str, content: str, subject: str | None = None, idempotency_key: str | None = None) -> Notification:
        async with self.lock:
            c = await self.cases.get(case_id)
            if channel not in {"IN_APP", "EMAIL", "SMS"} or not content.strip() or len(content) > 4000:
                raise fail("INVALID_INPUT", "Notification channel or content is invalid.")
            if idempotency_key:
                old = await self.provider.find_idempotent(idempotency_key)
                if old:
                    return old
            n = await self.provider.queue(
                Notification(
                    case_id=case_id, customer_id=c.customer_id, channel=channel, content=content.strip(), subject=subject, idempotency_key=idempotency_key
                )
            )
            await self.audit.record("NOTIFICATION_CREATED", n, c)
            return n


class SummaryService:
    def __init__(self, cases: CaseRepository, notes: CaseNoteRepository, approvals: ApprovalRepository, notifications: NotificationRepository) -> None:
        self.cases, self.notes, self.approvals, self.notifications = cases, notes, approvals, notifications

    async def generate(self, i: str) -> dict[str, Any]:
        c = await self.cases.get(i)
        n = await self.notes.list(i, 200)
        a = await self.approvals.list(i)
        o = await self.notifications.list(i)
        s = {"case": dump(c), "notes": [dump(x) for x in n], "approvals": [dump(x) for x in a], "notifications": [dump(x) for x in o]}
        text = f"Case {c.case_id} is {c.status} with {c.priority} priority. Issue: {c.title or c.description or 'No issue text recorded'}. Notes: {len(n)}. Approvals: {len(a)}. Notifications queued: {len(o)}. Resolution: {c.resolution or 'Not resolved'}."
        return {"structured_summary": s, "human_readable_summary": text}
