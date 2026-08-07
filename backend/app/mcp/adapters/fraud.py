"""Fraud MCP Adapter - Typed interface to Fraud MCP."""

from __future__ import annotations

import logging
from typing import Any

from app.mcp.protocol import MCPClient

logger = logging.getLogger(__name__)


class FraudMCPAdapter:
    """Typed adapter for Fraud MCP tools."""

    def __init__(self, mcp_client: MCPClient) -> None:
        self.client = mcp_client

    async def assess_transaction_risk(
        self,
        customer_id: str,
        transaction_id: str,
        device_id: str | None = None,
        ip_address: str | None = None,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Assess transaction fraud risk."""
        args: dict[str, Any] = {
            "customer_id": customer_id,
            "transaction_id": transaction_id,
        }

        if device_id:
            args["device_id"] = device_id
        if ip_address:
            args["ip_address"] = ip_address
        if channel:
            args["channel"] = channel

        return await self.client.call_tool("assess_transaction_risk", args)

    async def get_risk_assessment(
        self,
        assessment_id: str,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        """Get existing risk assessment."""
        args: dict[str, Any] = {"assessment_id": assessment_id}
        if customer_id:
            args["customer_id"] = customer_id

        return await self.client.call_tool("get_risk_assessment", args)

    async def get_customer_risk_context(
        self,
        customer_id: str,
        history_limit: int = 100,
    ) -> dict[str, Any]:
        """Get customer risk context."""
        return await self.client.call_tool(
            "get_customer_risk_context",
            {"customer_id": customer_id, "history_limit": history_limit},
        )

    async def explain_risk(
        self,
        assessment_id: str,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        """Get risk explanation."""
        args: dict[str, Any] = {"assessment_id": assessment_id}
        if customer_id:
            args["customer_id"] = customer_id

        return await self.client.call_tool("explain_risk", args)

    async def detect_transaction_anomalies(
        self,
        customer_id: str,
        transaction_ids: list[str],
    ) -> dict[str, Any]:
        """Detect transaction anomalies."""
        return await self.client.call_tool(
            "detect_transaction_anomalies",
            {"customer_id": customer_id, "transaction_ids": transaction_ids},
        )

    async def check_device(
        self,
        device_id: str,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        """Check device trust status."""
        args: dict[str, Any] = {"device_id": device_id}
        if customer_id:
            args["customer_id"] = customer_id

        return await self.client.call_tool("check_device", args)

    async def check_blacklist(
        self,
        entity_type: str,
        entity_value: str,
    ) -> dict[str, Any]:
        """Check blacklist."""
        return await self.client.call_tool(
            "check_blacklist",
            {"entity_type": entity_type, "entity_value": entity_value},
        )

    async def create_fraud_alert(
        self,
        customer_id: str,
        assessment_id: str,
        alert_type: str,
        severity: str,
        description: str,
    ) -> dict[str, Any]:
        """Create fraud alert."""
        return await self.client.call_tool(
            "create_fraud_alert",
            {
                "customer_id": customer_id,
                "assessment_id": assessment_id,
                "alert_type": alert_type,
                "severity": severity,
                "description": description,
            },
        )

    async def get_fraud_alert(self, alert_id: str) -> dict[str, Any]:
        """Get fraud alert."""
        return await self.client.call_tool("get_fraud_alert", {"alert_id": alert_id})

    async def get_fraud_alerts(
        self,
        customer_id: str,
        status: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get fraud alerts for customer."""
        args: dict[str, Any] = {"customer_id": customer_id, "limit": limit}
        if status:
            args["status"] = status

        return await self.client.call_tool("get_fraud_alerts", args)

    async def update_fraud_alert_status(
        self,
        alert_id: str,
        status: str,
        resolution_note: str | None = None,
    ) -> dict[str, Any]:
        """Update fraud alert status."""
        args: dict[str, Any] = {"alert_id": alert_id, "status": status}
        if resolution_note:
            args["resolution_note"] = resolution_note

        return await self.client.call_tool("update_fraud_alert_status", args)
