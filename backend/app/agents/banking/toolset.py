"""Banking Agent toolset."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.mcp.adapters.banking import BankingMCPAdapter


class BankingToolset:
    """Banking Agent tool definitions."""

    def __init__(self, banking_adapter: BankingMCPAdapter) -> None:
        self.banking_adapter = banking_adapter

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get LangChain-compatible tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_accounts",
                    "description": "Retrieve the customer's linked banking accounts and current balance information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer identifier",
                            }
                        },
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_account_summary",
                    "description": "Get account summary with counts and balance totals by currency.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer identifier",
                            }
                        },
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recent_transactions",
                    "description": "Get customer's recent banking transactions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string"},
                            "limit": {
                                "type": "integer",
                                "description": "Number of transactions (1-100)",
                                "default": 20,
                            },
                            "account_id": {
                                "type": "string",
                                "description": "Optional account filter",
                            },
                        },
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_transaction",
                    "description": "Get specific transaction by ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string"},
                            "transaction_id": {"type": "string"},
                        },
                        "required": ["customer_id", "transaction_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_transactions",
                    "description": "Search transaction history by merchant, amount, date, category.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string"},
                            "merchant": {"type": "string"},
                            "min_amount": {"type": "number"},
                            "max_amount": {"type": "number"},
                            "start_date": {"type": "string", "format": "date"},
                            "end_date": {"type": "string", "format": "date"},
                            "category": {"type": "string"},
                            "limit": {"type": "integer", "default": 100},
                        },
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "sync_transactions",
                    "description": "Synchronize transaction data from Plaid.",
                    "parameters": {
                        "type": "object",
                        "properties": {"customer_id": {"type": "string"}},
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_customer_identity",
                    "description": "Get verified customer identity information.",
                    "parameters": {
                        "type": "object",
                        "properties": {"customer_id": {"type": "string"}},
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_liabilities",
                    "description": "Get customer liabilities (loans, credit).",
                    "parameters": {
                        "type": "object",
                        "properties": {"customer_id": {"type": "string"}},
                        "required": ["customer_id"],
                    },
                },
            },
        ]

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a banking tool."""
        # Delegate to Banking MCP adapter
        if tool_name == "get_accounts":
            return await self.banking_adapter.get_accounts(arguments["customer_id"])
        elif tool_name == "get_account_summary":
            return await self.banking_adapter.get_account_summary(arguments["customer_id"])
        elif tool_name == "get_recent_transactions":
            return await self.banking_adapter.get_recent_transactions(
                arguments["customer_id"],
                limit=arguments.get("limit", 20),
                account_id=arguments.get("account_id"),
            )
        elif tool_name == "get_transaction":
            return await self.banking_adapter.get_transaction(
                arguments["customer_id"],
                arguments["transaction_id"],
            )
        elif tool_name == "search_transactions":
            return await self.banking_adapter.search_transactions(
                customer_id=arguments["customer_id"],
                merchant=arguments.get("merchant"),
                min_amount=arguments.get("min_amount"),
                max_amount=arguments.get("max_amount"),
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                category=arguments.get("category"),
                limit=arguments.get("limit", 100),
            )
        elif tool_name == "sync_transactions":
            return await self.banking_adapter.sync_transactions(arguments["customer_id"])
        elif tool_name == "get_customer_identity":
            return await self.banking_adapter.get_customer_identity(arguments["customer_id"])
        elif tool_name == "get_liabilities":
            return await self.banking_adapter.get_liabilities(arguments["customer_id"])
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
