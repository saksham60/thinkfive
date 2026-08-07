from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from fraudMCP.app.errors import (
    AlertNotFoundError,
    AssessmentNotFoundError,
    ConflictError,
    DuplicateAlertError,
    PersistenceUnavailableError,
)
from fraudMCP.app.models.alert import AlertStatus, AlertStatusEvent, FraudAlert
from fraudMCP.app.models.assessment import RiskAssessment


class SupabaseAssessmentRepository:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def create_assessment(self, assessment: RiskAssessment) -> RiskAssessment:
        row = {
            "assessment_id": assessment.assessment_id,
            "customer_id": assessment.customer_id,
            "transaction_id": assessment.transaction_id,
            "risk_score": assessment.risk_score,
            "severity": assessment.severity.value,
            "created_at": assessment.created_at.isoformat(),
            "payload": assessment.model_dump(mode="json"),
        }
        try:
            result = await asyncio.to_thread(lambda: self.client.table("fraud_assessments").insert(row).execute())
        except Exception:
            raise PersistenceUnavailableError("Fraud assessment persistence is unavailable.") from None
        return RiskAssessment.model_validate(result.data[0]["payload"])

    async def get_assessment(self, assessment_id: str) -> RiskAssessment:
        rows = await self._query({"assessment_id": assessment_id}, 1)
        if not rows:
            raise AssessmentNotFoundError("Risk assessment was not found.")
        return rows[0]

    async def list_customer_assessments(self, customer_id: str, limit: int = 100) -> tuple[RiskAssessment, ...]:
        return tuple(await self._query({"customer_id": customer_id}, max(1, min(limit, 200))))

    async def get_latest_assessment_for_transaction(self, customer_id: str, transaction_id: str) -> RiskAssessment | None:
        rows = await self._query({"customer_id": customer_id, "transaction_id": transaction_id}, 1)
        return rows[0] if rows else None

    async def count_customer_assessments(self, customer_id: str) -> int:
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table("fraud_assessments").select("assessment_id", count="exact").eq("customer_id", customer_id).execute()
            )
        except Exception:
            raise PersistenceUnavailableError("Fraud assessment persistence is unavailable.") from None
        return int(result.count or 0)

    async def _query(self, filters: dict[str, Any], limit: int) -> list[RiskAssessment]:
        def run() -> Any:
            query = self.client.table("fraud_assessments").select("payload")
            for key, value in filters.items():
                query = query.eq(key, value)
            return query.order("created_at", desc=True).limit(limit).execute()

        try:
            result = await asyncio.to_thread(run)
        except Exception:
            raise PersistenceUnavailableError("Fraud assessment persistence is unavailable.") from None
        return [RiskAssessment.model_validate(row["payload"]) for row in result.data]


class SupabaseFraudAlertRepository:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def create_alert(self, alert: FraudAlert) -> FraudAlert:
        row = self._row(alert)
        try:
            result = await asyncio.to_thread(lambda: self.client.table("fraud_alerts").insert(row).execute())
        except Exception:
            existing = await self.find_alert_by_transaction(alert.customer_id, alert.transaction_id)
            if existing:
                raise DuplicateAlertError("A fraud alert already exists for this customer transaction.") from None
            raise PersistenceUnavailableError("Fraud alert persistence is unavailable.") from None
        return FraudAlert.model_validate(result.data[0]["payload"])

    async def get_alert(self, alert_id: str) -> FraudAlert:
        rows = await self._query({"alert_id": alert_id}, 1)
        if not rows:
            raise AlertNotFoundError("Fraud alert was not found.")
        return rows[0]

    async def find_alert_by_transaction(self, customer_id: str, transaction_id: str) -> FraudAlert | None:
        rows = await self._query({"customer_id": customer_id, "transaction_id": transaction_id}, 1)
        return rows[0] if rows else None

    async def list_alerts(
        self,
        customer_id: str | None = None,
        status: AlertStatus | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> tuple[FraudAlert, ...]:
        filters: dict[str, Any] = {"customer_id": customer_id, "status": status.value if status else None, "severity": severity}
        return tuple(await self._query(filters, max(1, min(limit, 200))))

    async def update_status(self, alert_id: str, status: AlertStatus, note: str | None = None) -> FraudAlert:
        existing = await self.get_alert(alert_id)
        notes = (*existing.notes, note) if note else existing.notes
        changed_at = datetime.now(existing.updated_at.tzinfo)
        updated = existing.model_copy(
            update={
                "status": status,
                "updated_at": changed_at,
                "notes": notes,
                "history": (*existing.history, AlertStatusEvent(status=status, changed_at=changed_at, note=note)),
            }
        )
        return await self._conditional_update(existing, updated)

    async def add_evidence(self, alert_id: str, evidence: dict[str, Any]) -> FraudAlert:
        existing = await self.get_alert(alert_id)
        updated = existing.model_copy(update={"evidence": (*existing.evidence, evidence), "updated_at": datetime.now(existing.updated_at.tzinfo)})
        return await self._conditional_update(existing, updated)

    async def count_open_alerts(self, customer_id: str) -> int:
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table("fraud_alerts")
                .select("alert_id", count="exact")
                .eq("customer_id", customer_id)
                .eq("status", AlertStatus.OPEN.value)
                .execute()
            )
        except Exception:
            raise PersistenceUnavailableError("Fraud alert persistence is unavailable.") from None
        return int(result.count or 0)

    async def _conditional_update(self, before: FraudAlert, after: FraudAlert) -> FraudAlert:
        row = self._row(after)
        row.pop("alert_id")
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table("fraud_alerts").update(row).eq("alert_id", before.alert_id).eq("updated_at", before.updated_at.isoformat()).execute()
            )
        except Exception:
            raise PersistenceUnavailableError("Fraud alert persistence is unavailable.") from None
        if not result.data:
            raise ConflictError("Fraud alert changed concurrently; retry the operation.", code="CONCURRENT_ALERT_UPDATE", retryable=True)
        return FraudAlert.model_validate(result.data[0]["payload"])

    async def _query(self, filters: dict[str, Any], limit: int) -> list[FraudAlert]:
        def run() -> Any:
            query = self.client.table("fraud_alerts").select("payload")
            for key, value in filters.items():
                if value is not None:
                    query = query.eq(key, value)
            return query.order("created_at", desc=True).limit(limit).execute()

        try:
            result = await asyncio.to_thread(run)
        except Exception:
            raise PersistenceUnavailableError("Fraud alert persistence is unavailable.") from None
        return [FraudAlert.model_validate(row["payload"]) for row in result.data]

    @staticmethod
    def _row(alert: FraudAlert) -> dict[str, Any]:
        return {
            "alert_id": alert.alert_id,
            "assessment_id": alert.assessment_id,
            "customer_id": alert.customer_id,
            "transaction_id": alert.transaction_id,
            "risk_score": alert.risk_score,
            "severity": alert.severity.value,
            "priority": alert.priority.value,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat(),
            "payload": alert.model_dump(mode="json"),
        }
