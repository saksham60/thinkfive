from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from case.app.container import Container

from .common import response


def register(m: FastMCP, c: Container) -> None:
    @m.tool(
        description="Create a persistent customer-service or investigation case. Use when explicit workflow tracking is required; optional fraud and transaction references are validated by their source MCPs."
    )
    async def create_case(
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
    ) -> dict[str, Any]:
        return await response(
            lambda: c.case.create(
                customer_id, case_type, title, description, transaction_id, fraud_alert_id, assessment_id, priority, metadata, idempotency_key
            )
        )

    @m.tool(
        description="Create an idempotent persistent investigation case from a Fraud MCP alert. Use after an alert requires human workflow; this does not itself freeze a card."
    )
    async def create_case_from_fraud_alert(fraud_alert_id: str, title: str | None = None, description: str | None = None) -> dict[str, Any]:
        return await response(lambda: c.case.from_alert(fraud_alert_id, title, description))

    @m.tool(description="Retrieve a case with recent notes and approval summary. Use for detailed workflow context without the full audit trail.")
    async def get_case(case_id: str) -> dict[str, Any]:
        return await response(lambda: c.case.get(case_id))

    @m.tool(description="Retrieve compact case status, assignment, priority and pending-approval count for supervisor polling.")
    async def get_case_status(case_id: str) -> dict[str, Any]:
        return await response(lambda: c.case.status(case_id))

    @m.tool(description="Search bounded persistent cases for supervisor dashboards using customer, workflow, assignment, fraud or transaction filters.")
    async def search_cases(
        customer_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: str | None = None,
        case_type: str | None = None,
        fraud_alert_id: str | None = None,
        transaction_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        return await response(
            lambda: c.case.search(
                limit,
                customer_id=customer_id,
                status=status,
                priority=priority,
                assigned_to=assigned_to,
                case_type=case_type,
                fraud_alert_id=fraud_alert_id,
                transaction_id=transaction_id,
            )
        )

    @m.tool(description="Update editable case fields through the strict case state machine. Use for explicit workflow changes; closed cases cannot be changed.")
    async def update_case(
        case_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        assigned_to: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await response(
            lambda: c.case.update(case_id, title=title, description=description, priority=priority, status=status, assigned_to=assigned_to, metadata=metadata)
        )

    @m.tool(description="Assign a case to a workflow identifier and triage a newly open case. No real staff identity is hardcoded.")
    async def assign_case(case_id: str, assignee: str) -> dict[str, Any]:
        return await response(lambda: c.case.assign(case_id, assignee))

    @m.tool(description="Resolve a case with required grounded resolution text and a recorded actor.")
    async def resolve_case(case_id: str, resolution: str, resolved_by: str) -> dict[str, Any]:
        return await response(lambda: c.case.resolve(case_id, resolution, resolved_by))

    @m.tool(description="Close a resolved case after confirming a resolution exists and no approvals remain pending.")
    async def close_case(case_id: str, closed_by: str) -> dict[str, Any]:
        return await response(lambda: c.case.close(case_id, closed_by))
