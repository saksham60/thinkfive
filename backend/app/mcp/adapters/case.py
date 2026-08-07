"""Case MCP Adapter - Typed interface to Case MCP."""

from __future__ import annotations

import logging
from typing import Any

from app.mcp.protocol import MCPClient

logger = logging.getLogger(__name__)


class CaseMCPAdapter:
    """Typed adapter for Case MCP tools."""

    def __init__(self, mcp_client: MCPClient) -> None:
        self.client = mcp_client

    async def create_case(
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
    ) -> dict[str, Any]:
        """Create a new case."""
        args: dict[str, Any] = {
            "customer_id": customer_id,
            "case_type": case_type,
        }
        optional = {
            "title": title, "description": description, "transaction_id": transaction_id,
            "fraud_alert_id": fraud_alert_id, "assessment_id": assessment_id,
            "priority": priority, "metadata": metadata, "idempotency_key": idempotency_key,
        }
        args.update({key: value for key, value in optional.items() if value is not None})

        return await self.client.call_tool("create_case", args)

    async def create_case_from_fraud_alert(
        self,
        fraud_alert_id: str,
        title: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create case from fraud alert."""
        args: dict[str, Any] = {"fraud_alert_id": fraud_alert_id}
        if title:
            args["title"] = title
        if description:
            args["description"] = description

        return await self.client.call_tool("create_case_from_fraud_alert", args)

    async def get_case(self, case_id: str) -> dict[str, Any]:
        """Get case details."""
        return await self.client.call_tool("get_case", {"case_id": case_id})

    async def update_case(
        self,
        case_id: str,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: str | None = None,
    ) -> dict[str, Any]:
        """Update case."""
        args: dict[str, Any] = {"case_id": case_id}
        if status:
            args["status"] = status
        if priority:
            args["priority"] = priority
        if assigned_to:
            args["assigned_to"] = assigned_to

        return await self.client.call_tool("update_case", args)

    async def add_case_note(
        self,
        case_id: str,
        content: str,
        note_type: str = "GENERAL",
        author_type: str = "AGENT",
        author_id: str | None = None,
    ) -> dict[str, Any]:
        """Add note to case."""
        args: dict[str, Any] = {
            "case_id": case_id,
            "content": content,
            "note_type": note_type,
            "author_type": author_type,
        }
        if author_id:
            args["author_id"] = author_id

        return await self.client.call_tool("add_case_note", args)

    async def search_cases(
        self,
        customer_id: str | None = None,
        status: str | None = None,
        case_type: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search cases."""
        args: dict[str, Any] = {"limit": limit}
        if customer_id:
            args["customer_id"] = customer_id
        if status:
            args["status"] = status
        if case_type:
            args["case_type"] = case_type

        return await self.client.call_tool("search_cases", args)

    async def request_approval(
        self,
        case_id: str,
        action_type: str,
        action_payload: dict[str, Any],
        requested_by: str = "agent",
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Request human approval for sensitive action."""
        args: dict[str, Any] = {
            "case_id": case_id,
            "action_type": action_type,
            "action_payload": action_payload,
            "requested_by": requested_by,
        }
        if idempotency_key:
            args["idempotency_key"] = idempotency_key

        return await self.client.call_tool("request_approval", args)

    async def approve_action(
        self,
        approval_id: str,
        reviewed_by: str,
        note: str | None = None,
        reviewer_role: str = "HUMAN_REVIEWER",
    ) -> dict[str, Any]:
        """Approve pending action (HUMAN ONLY - not for autonomous agents)."""
        args: dict[str, Any] = {
            "approval_id": approval_id,
            "reviewed_by": reviewed_by,
            "reviewer_role": reviewer_role,
        }
        if note:
            args["note"] = note

        return await self.client.call_tool("approve_action", args)

    async def reject_action(
        self,
        approval_id: str,
        reviewed_by: str,
        note: str | None = None,
        reviewer_role: str = "HUMAN_REVIEWER",
    ) -> dict[str, Any]:
        """Reject pending action (HUMAN ONLY - not for autonomous agents)."""
        args: dict[str, Any] = {
            "approval_id": approval_id,
            "reviewed_by": reviewed_by,
            "reviewer_role": reviewer_role,
        }
        if note:
            args["note"] = note

        return await self.client.call_tool("reject_action", args)

    async def get_card_status(
        self,
        customer_id: str,
        card_id: str,
    ) -> dict[str, Any]:
        """Get card status."""
        return await self.client.call_tool(
            "get_card_status",
            {"customer_id": customer_id, "card_id": card_id},
        )

    async def send_customer_notification(
        self,
        case_id: str,
        channel: str,
        content: str,
        subject: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Send customer notification."""
        args: dict[str, Any] = {"case_id": case_id, "channel": channel, "content": content}
        if subject is not None:
            args["subject"] = subject
        if idempotency_key is not None:
            args["idempotency_key"] = idempotency_key
        return await self.client.call_tool("send_customer_notification", args)
