from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from plaidbanking.app.container import Container

from .common import tool_response


def register_liability_tools(mcp: FastMCP, container: Container) -> None:
    source = container.source

    @mcp.tool(
        description="Retrieve liabilities when supported by the configured banking provider; otherwise returns capability_available=false."
    )
    async def get_liabilities(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.banking.get_liabilities(customer_id))
