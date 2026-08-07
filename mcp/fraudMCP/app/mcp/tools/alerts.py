from __future__ import annotations

from typing import Any

from fraudMCP.app.container import Container
from fraudMCP.app.models.alert import FraudAlert

from .common import tool_response


def register_alert_tools(mcp: Any, container: Container) -> None:
    source = "fraud_engine"

    @mcp.tool(
        description=(
            "Create a fraud alert from an existing qualifying risk assessment. "
            "Use after assess_transaction_risk when the score exceeds the configured alert threshold. "
            "This tool does not create customer-service cases."
        )
    )
    async def create_fraud_alert(assessment_id: str, customer_id: str | None = None) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            alert = await container.alert_service.create_fraud_alert(assessment_id, customer_id=customer_id)
            return _alert_summary(alert)

        return await tool_response(customer_id=customer_id, source=source, tool_name="create_fraud_alert", operation=run)

    @mcp.tool(description="Retrieve one fraud alert and its linked assessment evidence. Use when reviewing an alert in detail.")
    async def get_fraud_alert(alert_id: str, customer_id: str | None = None) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            alert = await container.alert_service.get_fraud_alert(alert_id, customer_id=customer_id)
            assessment = await container.fraud_service.get_risk_assessment(alert.assessment_id, customer_id=customer_id)
            payload = _alert_detail(alert)
            payload["assessment"] = {
                "assessment_id": assessment.assessment_id,
                "risk_score": assessment.risk_score,
                "severity": assessment.severity.value,
                "evidence": assessment.evidence,
                "signals": [
                    {
                        "feature": item.feature,
                        "score": item.score,
                        "contribution": item.contribution,
                        "evidence": item.evidence,
                    }
                    for item in assessment.feature_values
                    if item.available and item.score is not None and item.score >= 0.35
                ],
            }
            return payload

        return await tool_response(customer_id=customer_id, source=source, tool_name="get_fraud_alert", operation=run)

    @mcp.tool(
        description=("List fraud alerts with optional customer/status/severity filters. Use for supervisor dashboard and triage queues with bounded results.")
    )
    async def get_fraud_alerts(
        customer_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            alerts = await container.alert_service.get_fraud_alerts(customer_id=customer_id, status=status, severity=severity, limit=limit)
            return {
                "count": len(alerts),
                "results": [_alert_summary(alert) for alert in alerts],
            }

        return await tool_response(customer_id=customer_id, source=source, tool_name="get_fraud_alerts", operation=run)

    @mcp.tool(
        description=(
            "Update fraud alert workflow status. Use for transitions such as OPEN -> INVESTIGATING or INVESTIGATING -> ESCALATED/RESOLVED/FALSE_POSITIVE."
        )
    )
    async def update_fraud_alert_status(alert_id: str, status: str, note: str | None = None, customer_id: str | None = None) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            alert = await container.alert_service.update_fraud_alert_status(alert_id, status, note=note, customer_id=customer_id)
            return _alert_detail(alert)

        return await tool_response(customer_id=customer_id, source=source, tool_name="update_fraud_alert_status", operation=run)


def _alert_summary(alert: FraudAlert) -> dict[str, Any]:
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
    }


def _alert_detail(alert: FraudAlert) -> dict[str, Any]:
    return {
        **_alert_summary(alert),
        "updated_at": alert.updated_at.isoformat(),
        "notes": list(alert.notes),
        "history": [item.model_dump(mode="json", exclude_none=True) for item in alert.history],
        "evidence": list(alert.evidence),
    }
