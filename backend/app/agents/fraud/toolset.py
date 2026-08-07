"""Fraud Agent toolset."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.constants import CANONICAL_CUSTOMER_ID

if TYPE_CHECKING:
    from app.mcp.adapters.fraud import FraudMCPAdapter


class FraudToolset:
    """Fraud Agent tool definitions - autonomous, non-sensitive tools only."""

    def __init__(self, fraud_adapter: FraudMCPAdapter, customer_id: str = CANONICAL_CUSTOMER_ID) -> None:
        self.fraud_adapter = fraud_adapter
        self.customer_id = customer_id

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "assess_transaction_risk",
                    "description": "Analyze a specific transaction for fraud risk.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "transaction_id": {"type": "string"},
                            "device_id": {"type": "string"},
                            "channel": {"type": "string"},
                        },
                        "required": ["transaction_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_customer_risk_context",
                    "description": "Get customer behavioral risk context and open-alert history.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "history_limit": {"type": "integer", "default": 100},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_transaction_anomalies",
                    "description": "Detect statistical anomalies across a set of transactions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "transaction_limit": {"type": "integer", "default": 100},
                            "max_results": {"type": "integer", "default": 20},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_device",
                    "description": "Check device trust status.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {"type": "string"},
                        },
                        "required": ["device_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_blacklist",
                    "description": "Check if an entity (merchant, device, IP) is blacklisted.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_type": {"type": "string"},
                            "value": {"type": "string"},
                        },
                        "required": ["entity_type", "value"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_fraud_alert",
                    "description": "Create a fraud alert from a risk assessment.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "assessment_id": {"type": "string"},
                        },
                        "required": ["assessment_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_fraud_alerts",
                    "description": "Retrieve fraud alerts for a customer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_fraud_alert_status",
                    "description": "Update fraud alert status (e.g., to FALSE_POSITIVE when customer confirms legitimacy).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "alert_id": {"type": "string"},
                            "status": {"type": "string"},
                            "note": {"type": "string"},
                        },
                        "required": ["alert_id", "status"],
                    },
                },
            },
        ]

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        adapter = self.fraud_adapter
        if tool_name == "assess_transaction_risk":
            return await adapter.assess_transaction_risk(
                customer_id=self.customer_id,
                transaction_id=arguments["transaction_id"],
                device_id=arguments.get("device_id"),
                channel=arguments.get("channel"),
            )
        elif tool_name == "get_customer_risk_context":
            return await adapter.get_customer_risk_context(
                self.customer_id, arguments.get("history_limit", 100)
            )
        elif tool_name == "detect_transaction_anomalies":
            return await adapter.detect_transaction_anomalies(
                self.customer_id, arguments.get("transaction_limit", 100), arguments.get("max_results", 20)
            )
        elif tool_name == "check_device":
            return await adapter.check_device(self.customer_id, arguments["device_id"])
        elif tool_name == "check_blacklist":
            return await adapter.check_blacklist(arguments["entity_type"], arguments["value"])
        elif tool_name == "create_fraud_alert":
            return await adapter.create_fraud_alert(
                assessment_id=arguments["assessment_id"],
                customer_id=self.customer_id,
            )
        elif tool_name == "get_fraud_alerts":
            return await adapter.get_fraud_alerts(self.customer_id, arguments.get("status"))
        elif tool_name == "update_fraud_alert_status":
            return await adapter.update_fraud_alert_status(
                arguments["alert_id"], arguments["status"], arguments.get("note"), self.customer_id
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
