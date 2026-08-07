from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from plaidbanking.app.container import Container

from .common import tool_response


def register_account_tools(mcp: FastMCP, container: Container) -> None:
    source = f"plaid_{container.settings.plaid_env}"

    @mcp.tool(
        description="Retrieve the customer's linked banking accounts and current balance information. Use when account names, types, masks, or balances are needed."
    )
    async def get_accounts(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.banking.get_accounts(customer_id, balance=True))

    @mcp.tool(
        description="Summarize the customer's linked accounts with counts and currency-separated balance totals. Use for an account-level overview; currencies are never combined."
    )
    async def get_account_summary(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.banking.get_account_summary(customer_id))

    @mcp.tool(
        description="Retrieve the current and available balance for one account owned by the customer. Use when the account ID is known and an exact balance is required."
    )
    async def get_account_balance(customer_id: str, account_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.banking.get_account_balance(customer_id, account_id))

    @mcp.tool(
        description="Inspect safe Plaid Item connection health, enabled products, and transaction synchronization freshness. This never returns Plaid access credentials."
    )
    async def get_banking_connection_status(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.banking.connection_status(customer_id))
