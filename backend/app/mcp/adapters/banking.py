"""Banking MCP Adapter - Typed interface to Banking MCP."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from app.mcp.protocol import MCPClient

logger = logging.getLogger(__name__)


class BankingMCPAdapter:
    """Typed adapter for Banking MCP tools."""

    def __init__(self, mcp_client: MCPClient) -> None:
        self.client = mcp_client

    async def get_accounts(self, customer_id: str) -> dict[str, Any]:
        """Get customer accounts with balances."""
        return await self.client.call_tool(
            "get_accounts",
            {"customer_id": customer_id},
        )

    async def get_account_summary(self, customer_id: str) -> dict[str, Any]:
        """Get account summary with totals."""
        return await self.client.call_tool(
            "get_account_summary",
            {"customer_id": customer_id},
        )

    async def get_account_balance(
        self,
        customer_id: str,
        account_id: str,
    ) -> dict[str, Any]:
        """Get specific account balance."""
        return await self.client.call_tool(
            "get_account_balance",
            {"customer_id": customer_id, "account_id": account_id},
        )

    async def get_recent_transactions(
        self,
        customer_id: str,
        limit: int = 20,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        """Get recent transactions."""
        args: dict[str, Any] = {
            "customer_id": customer_id,
            "limit": limit,
        }
        if account_id:
            args["account_id"] = account_id

        return await self.client.call_tool("get_recent_transactions", args)

    async def get_transaction(
        self,
        customer_id: str,
        transaction_id: str,
    ) -> dict[str, Any]:
        """Get specific transaction."""
        return await self.client.call_tool(
            "get_transaction",
            {"customer_id": customer_id, "transaction_id": transaction_id},
        )

    async def search_transactions(
        self,
        customer_id: str,
        merchant: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Search transaction history."""
        args: dict[str, Any] = {
            "customer_id": customer_id,
            "limit": limit,
        }

        if merchant:
            args["merchant"] = merchant
        if min_amount is not None:
            args["min_amount"] = min_amount
        if max_amount is not None:
            args["max_amount"] = max_amount
        if start_date:
            args["start_date"] = str(start_date) if isinstance(start_date, date) else start_date
        if end_date:
            args["end_date"] = str(end_date) if isinstance(end_date, date) else end_date
        if category:
            args["category"] = category

        return await self.client.call_tool("search_transactions", args)

    async def sync_transactions(self, customer_id: str) -> dict[str, Any]:
        """Sync transactions from Plaid."""
        return await self.client.call_tool(
            "sync_transactions",
            {"customer_id": customer_id},
        )

    async def get_customer_identity(self, customer_id: str) -> dict[str, Any]:
        """Get customer identity information."""
        return await self.client.call_tool(
            "get_customer_identity",
            {"customer_id": customer_id},
        )

    async def get_liabilities(self, customer_id: str) -> dict[str, Any]:
        """Get customer liabilities."""
        return await self.client.call_tool(
            "get_liabilities",
            {"customer_id": customer_id},
        )

    async def get_banking_connection_status(self, customer_id: str) -> dict[str, Any]:
        """Get Plaid connection status."""
        return await self.client.call_tool(
            "get_banking_connection_status",
            {"customer_id": customer_id},
        )
