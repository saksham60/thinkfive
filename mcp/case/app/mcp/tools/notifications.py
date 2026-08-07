from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from case.app.container import Container

from .common import response


def register(m: FastMCP, c: Container) -> None:
    @m.tool(description="Create a Supabase outbox notification for an existing case. Phase 3 records simulated delivery and does not claim external delivery.")
    async def send_customer_notification(
        case_id: str, channel: str, content: str, subject: str | None = None, idempotency_key: str | None = None
    ) -> dict[str, Any]:
        return await response(lambda: c.notification.send(case_id, channel, content, subject, idempotency_key))

    @m.tool(description="Create an EMAIL notification in the Supabase outbox. No external email provider delivery is claimed.")
    async def send_email(case_id: str, subject: str, content: str, idempotency_key: str | None = None) -> dict[str, Any]:
        return await response(lambda: c.notification.send(case_id, "EMAIL", content, subject, idempotency_key))

    @m.tool(description="Create an SMS notification in the Supabase outbox. No external SMS provider delivery is claimed.")
    async def send_sms(case_id: str, content: str, idempotency_key: str | None = None) -> dict[str, Any]:
        return await response(lambda: c.notification.send(case_id, "SMS", content, None, idempotency_key))

    @m.tool(description="Produce a deterministic grounded case summary from stored case, notes, approvals, notifications and resolution without an LLM.")
    async def generate_case_summary(case_id: str) -> dict[str, Any]:
        return await response(lambda: c.summary.generate(case_id))

    @m.tool(description="Retrieve ordered append-only audit events for compliance, explainability and supervisor review.")
    async def get_audit_trail(case_id: str, limit: int = 200) -> dict[str, Any]:
        return await response(lambda: c.case.history(case_id, limit))
