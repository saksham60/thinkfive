from __future__ import annotations

from datetime import date
from typing import Any

from fastmcp import FastMCP

from plaidbanking.app.container import Container

from .common import tool_response


def register_sandbox_tools(mcp: FastMCP, container: Container) -> None:
    source = container.source

    @mcp.tool(description="Create a durable synthetic transaction for the configured demo banking provider. This moves no real money.")
    async def simulate_transaction(customer_id: str, amount: float, description: str, date: date | None = None) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.sandbox.simulate_transaction(customer_id, amount, description, date))

    @mcp.tool(description="Request a synthetic transaction webhook when supported by the configured banking provider.")
    async def fire_transaction_webhook(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.sandbox.fire_webhook(customer_id))

    @mcp.tool(
        description="Create suspicious-looking synthetic banking data for later assessment by Fraud MCP. This performs data simulation only and never labels fraud."
    )
    async def create_demo_fraud_scenario(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.sandbox.create_demo_fraud_scenario(customer_id))
