from __future__ import annotations

from typing import Any

from fraudMCP.app.container import Container
from fraudMCP.app.models.assessment import RiskAssessment

from .common import tool_response


def register_assessment_tools(mcp: Any, container: Container) -> None:
    source = "fraud_engine"

    @mcp.tool(
        description=(
            "Analyze a specific banking transaction using customer transaction history, behavioral patterns, "
            "optional device context, blacklist checks, and statistical anomaly signals. "
            "Use when a transaction needs fraud-risk evaluation. "
            "This tool returns risk evidence but does not freeze cards or create cases."
        )
    )
    async def assess_transaction_risk(
        customer_id: str,
        transaction_id: str,
        device_id: str | None = None,
        ip_address: str | None = None,
        channel: str | None = None,
    ) -> dict[str, Any]:
        async def run(request_id: str) -> dict[str, Any]:
            assessment = await container.fraud_service.assess_transaction_risk(
                customer_id,
                transaction_id,
                device_id=device_id,
                ip_address=ip_address,
                channel=channel,
                request_id=request_id,
                persist=True,
            )
            return _assessment_payload(assessment)

        return await tool_response(customer_id=customer_id, source=source, tool_name="assess_transaction_risk", operation=run)

    @mcp.tool(
        description=(
            "Retrieve a previously generated risk assessment by assessment_id. "
            "Use when follow-up evidence review is needed after a prior transaction assessment."
        )
    )
    async def get_risk_assessment(assessment_id: str, customer_id: str | None = None) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            assessment = await container.fraud_service.get_risk_assessment(assessment_id, customer_id)
            return _assessment_payload(assessment, include_features=True)

        return await tool_response(customer_id=customer_id, source=source, tool_name="get_risk_assessment", operation=run)

    @mcp.tool(
        description=(
            "Build derived customer fraud context from recent banking behavior and fraud history. "
            "Use before escalation decisions when behavioral baselines and open-alert context are needed."
        )
    )
    async def get_customer_risk_context(customer_id: str, history_limit: int = 100) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            return await container.fraud_service.get_customer_risk_context(customer_id, history_limit=history_limit)

        return await tool_response(customer_id=customer_id, source=source, tool_name="get_customer_risk_context", operation=run)

    @mcp.tool(
        description=(
            "Produce a concise explanation for a stored risk assessment using only recorded evidence. "
            "Use for supervisor reasoning, investigator UI, or human review summaries."
        )
    )
    async def explain_risk(assessment_id: str, customer_id: str | None = None) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            return await container.fraud_service.explain_risk(assessment_id, customer_id)

        return await tool_response(customer_id=customer_id, source=source, tool_name="explain_risk", operation=run)


def _assessment_payload(assessment: RiskAssessment, *, include_features: bool = False) -> dict[str, Any]:
    signals = [
        {
            "feature": item.feature,
            "score": item.score,
            "contribution": item.contribution,
            "evidence": item.evidence,
        }
        for item in assessment.feature_values
        if item.available and item.score is not None and item.score >= 0.35
    ]

    payload: dict[str, Any] = {
        "assessment_id": assessment.assessment_id,
        "customer_id": assessment.customer_id,
        "transaction_id": assessment.transaction_id,
        "risk_score": assessment.risk_score,
        "severity": assessment.severity.value,
        "signals": signals,
        "evidence": assessment.evidence,
        "scorer_name": assessment.scorer_name,
        "scorer_version": assessment.scorer_version,
        "feature_schema_version": assessment.feature_schema_version,
        "assessed_at": assessment.created_at.isoformat(),
        "data_source": "fraud_engine",
        "warnings": list(assessment.warnings),
        "recommended_action": assessment.recommended_action,
    }
    if include_features:
        payload["feature_values"] = [item.model_dump(mode="json", exclude_none=True) for item in assessment.feature_values]
        payload["thresholds"] = assessment.thresholds.model_dump(mode="json")
    return payload
