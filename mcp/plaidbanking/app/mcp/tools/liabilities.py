from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from plaidbanking.app.container import Container

from .common import tool_response


def register_liability_tools(mcp: FastMCP, container: Container) -> None:
    source = f"plaid_{container.settings.plaid_env}"

    @mcp.tool(
        description="Retrieve available credit-card, mortgage, and student-loan liabilities from Plaid. Returns capability_available=false when the product is not enabled."
    )
    async def get_liabilities(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.banking.get_liabilities(customer_id))
