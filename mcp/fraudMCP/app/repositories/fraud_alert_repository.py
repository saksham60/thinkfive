from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Protocol

from fraudMCP.app.errors import AlertNotFoundError
from fraudMCP.app.models.alert import AlertStatus, AlertStatusEvent, FraudAlert


class FraudAlertRepository(Protocol):
    async def create_alert(self, alert: FraudAlert) -> FraudAlert: ...

    async def get_alert(self, alert_id: str) -> FraudAlert: ...

    async def find_alert_by_transaction(self, customer_id: str, transaction_id: str) -> FraudAlert | None: ...

    async def list_alerts(
        self, customer_id: str | None = None, status: AlertStatus | None = None, severity: str | None = None, limit: int = 100
    ) -> tuple[FraudAlert, ...]: ...

    async def update_status(self, alert_id: str, status: AlertStatus, note: str | None = None) -> FraudAlert: ...

    async def add_evidence(self, alert_id: str, evidence: dict[str, Any]) -> FraudAlert: ...

    async def count_open_alerts(self, customer_id: str) -> int: ...


class InMemoryFraudAlertRepository(FraudAlertRepository):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._alerts: dict[str, FraudAlert] = {}
        self._customer_index: dict[str, list[str]] = defaultdict(list)
        self._transaction_index: dict[tuple[str, str], str] = {}

    async def create_alert(self, alert: FraudAlert) -> FraudAlert:
        async with self._lock:
            self._alerts[alert.alert_id] = alert
            self._customer_index[alert.customer_id].append(alert.alert_id)
            self._transaction_index[(alert.customer_id, alert.transaction_id)] = alert.alert_id
        return alert

    async def get_alert(self, alert_id: str) -> FraudAlert:
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise AlertNotFoundError("Fraud alert was not found.")
        return alert

    async def find_alert_by_transaction(self, customer_id: str, transaction_id: str) -> FraudAlert | None:
        alert_id = self._transaction_index.get((customer_id, transaction_id))
        if not alert_id:
            return None
        return self._alerts.get(alert_id)

    async def list_alerts(
        self, customer_id: str | None = None, status: AlertStatus | None = None, severity: str | None = None, limit: int = 100
    ) -> tuple[FraudAlert, ...]:
        bounded = max(1, min(limit, 200))
        if customer_id:
            ids = self._customer_index.get(customer_id, [])
            candidates = [self._alerts[item_id] for item_id in ids]
        else:
            candidates = list(self._alerts.values())

        filtered: list[FraudAlert] = []
        for alert in candidates:
            if status is not None and alert.status != status:
                continue
            if severity is not None and alert.severity.value != severity:
                continue
            filtered.append(alert)

        filtered.sort(key=lambda item: item.created_at, reverse=True)
        return tuple(filtered[:bounded])

    async def update_status(self, alert_id: str, status: AlertStatus, note: str | None = None) -> FraudAlert:
        async with self._lock:
            existing = self._alerts.get(alert_id)
            if existing is None:
                raise AlertNotFoundError("Fraud alert was not found.")

            notes = list(existing.notes)
            if note:
                notes.append(note)
            history = list(existing.history)
            history.append(AlertStatusEvent(status=status, changed_at=datetime.now(existing.created_at.tzinfo), note=note))

            updated = existing.model_copy(
                update={
                    "status": status,
                    "updated_at": datetime.now(existing.updated_at.tzinfo),
                    "notes": tuple(notes),
                    "history": tuple(history),
                }
            )
            self._alerts[alert_id] = updated
            return updated

    async def add_evidence(self, alert_id: str, evidence: dict[str, Any]) -> FraudAlert:
        async with self._lock:
            existing = self._alerts.get(alert_id)
            if existing is None:
                raise AlertNotFoundError("Fraud alert was not found.")

            payload = list(existing.evidence)
            payload.append(evidence)
            updated = existing.model_copy(update={"evidence": tuple(payload), "updated_at": datetime.now(existing.updated_at.tzinfo)})
            self._alerts[alert_id] = updated
            return updated

    async def count_open_alerts(self, customer_id: str) -> int:
        alerts = await self.list_alerts(customer_id=customer_id, status=AlertStatus.OPEN, limit=200)
        return len(alerts)
