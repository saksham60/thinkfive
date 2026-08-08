from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from fastmcp import FastMCP

from plaidbanking.app.container import Container
from plaidbanking.app.models.transaction import TransactionSearchFilters

from .common import tool_response


def register_transaction_tools(mcp: FastMCP, container: Container) -> None:
    source = container.source

    @mcp.tool(
        description="Synchronize the customer's transaction repository with its configured banking provider."
    )
    async def sync_transactions(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.transaction_service.sync(customer_id))

    @mcp.tool(
        description="Retrieve the customer's most recent synchronized banking transactions. Use when investigating recent purchases, withdrawals, transfers, charges, or unrecognized activity."
    )
    async def get_recent_transactions(customer_id: str, limit: int = 20, account_id: str | None = None) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            return await tool_response(customer_id, source, lambda: _invalid_limit())
        return await tool_response(customer_id, source, lambda: container.transaction_service.recent(customer_id, limit, account_id))

    @mcp.tool(
        description="Retrieve one specific transaction belonging to a customer after ensuring data is synchronized. Use when a transaction ID is already known."
    )
    async def get_transaction(customer_id: str, transaction_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.transaction_service.get(customer_id, transaction_id))

    @mcp.tool(
        description="Search locally synchronized transaction history by merchant, amount, date, category, account, and pending state. This is repository search, not a native Plaid arbitrary-search API."
    )
    async def search_transactions(
        customer_id: str,
        account_id: str | None = None,
        merchant: str | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        category: str | None = None,
        pending: bool | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        async def run() -> Any:
            filters = TransactionSearchFilters(
                account_id=account_id,
                merchant=merchant,
                min_amount=min_amount,
                max_amount=max_amount,
                start_date=start_date,
                end_date=end_date,
                category=category,
                pending=pending,
                limit=limit,
            )
            return await container.transaction_service.search(customer_id, filters)

        return await tool_response(customer_id, source, run)

    @mcp.tool(
        description="Request a transaction refresh from the configured banking provider when that capability is available."
    )
    async def refresh_transactions(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.transaction_service.refresh(customer_id))


async def _invalid_limit() -> Any:
    raise ValueError("limit must be between 1 and 100")
