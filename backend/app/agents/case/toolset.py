"""Case Agent toolset.

SECURITY: This toolset MUST NEVER include approve_action, reject_action,
freeze_card, unfreeze_card, or block_card. Those are reserved for the
trusted HumanActionService, invoked only from authenticated human REST
endpoints - never from the autonomous LLM tool-calling loop.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.constants import CANONICAL_CUSTOMER_ID

if TYPE_CHECKING:
    from app.mcp.adapters.case import CaseMCPAdapter

# Explicit safety allowlist - the only tool names this toolset will execute.
AUTONOMOUS_ALLOWED_TOOLS = frozenset(
    [
        "create_case",
        "create_case_from_fraud_alert",
        "get_case",
        "search_cases",
        "update_case",
        "add_case_note",
        "request_approval",
        "send_customer_notification",
    ]
)

# Tools that must NEVER be reachable from this autonomous toolset.
FORBIDDEN_TOOLS = frozenset(
    [
        "approve_action",
        "reject_action",
        "freeze_card",
        "unfreeze_card",
        "block_card",
    ]
)


class CaseToolset:
    """Case Agent tool definitions - excludes sensitive human-only actions."""

    def __init__(self, case_adapter: CaseMCPAdapter, customer_id: str = CANONICAL_CUSTOMER_ID) -> None:
        self.case_adapter = case_adapter
        self.customer_id = customer_id

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_case",
                    "description": "Create a new case.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "case_type": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "priority": {"type": "string", "default": "MEDIUM"},
                        },
                        "required": ["case_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_case_from_fraud_alert",
                    "description": "Create a case directly from an existing fraud alert.",
                    "parameters": {
                        "type": "object",
                        "properties": {"fraud_alert_id": {"type": "string"}, "title": {"type": "string"}, "description": {"type": "string"}},
                        "required": ["fraud_alert_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_case",
                    "description": "Get case details by ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {"case_id": {"type": "string"}},
                        "required": ["case_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_cases",
                    "description": "Search cases by customer/status/type.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "case_type": {"type": "string"},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "add_case_note",
                    "description": "Add an investigation note to a case.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "case_id": {"type": "string"},
                            "content": {"type": "string"},
                            "note_type": {"type": "string", "default": "GENERAL"},
                        },
                        "required": ["case_id", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "request_approval",
                    "description": (
                        "Request human authorization for a sensitive card action "
                        "(FREEZE_CARD, UNFREEZE_CARD, BLOCK_CARD). This does NOT execute the action."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "case_id": {"type": "string"},
                            "action_type": {"type": "string"},
                            "action_payload": {"type": "object"},
                        },
                        "required": ["case_id", "action_type", "action_payload"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_customer_notification",
                    "description": "Send a notification to the customer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "case_id": {"type": "string"},
                            "channel": {"type": "string"},
                            "content": {"type": "string"},
                            "subject": {"type": "string"},
                        },
                        "required": ["case_id", "channel", "content"],
                    },
                },
            },
        ]

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name in FORBIDDEN_TOOLS:
            raise PermissionError(
                f"Tool '{tool_name}' is forbidden for autonomous Case Agent - requires human approval workflow"
            )
        if tool_name not in AUTONOMOUS_ALLOWED_TOOLS:
            raise ValueError(f"Unknown or disallowed tool: {tool_name}")

        adapter = self.case_adapter
        if tool_name == "create_case":
            return await adapter.create_case(customer_id=self.customer_id, **arguments)
        elif tool_name == "create_case_from_fraud_alert":
            return await adapter.create_case_from_fraud_alert(**arguments)
        elif tool_name == "get_case":
            return await adapter.get_case(arguments["case_id"])
        elif tool_name == "search_cases":
            return await adapter.search_cases(customer_id=self.customer_id, **arguments)
        elif tool_name == "add_case_note":
            return await adapter.add_case_note(**arguments)
        elif tool_name == "request_approval":
            return await adapter.request_approval(**arguments)
        elif tool_name == "send_customer_notification":
            return await adapter.send_customer_notification(**arguments)

        raise ValueError(f"Unhandled tool: {tool_name}")
