from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from plaidbanking.app.container import Container

from .common import tool_response


def register_identity_tools(mcp: FastMCP, container: Container) -> None:
    source = container.source

    @mcp.tool(
        description="Retrieve customer identity data when supported by the configured banking provider."
    )
    async def get_customer_identity(customer_id: str) -> dict[str, Any]:
        return await tool_response(customer_id, source, lambda: container.banking.get_identity(customer_id))

    @mcp.tool(
        description="Compare customer-supplied identity attributes when supported by the configured banking provider."
    )
    async def verify_customer_identity(
        customer_id: str, name: str | None = None, phone: str | None = None, email: str | None = None, address: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await tool_response(
            customer_id,
            source,
            lambda: container.banking.verify_identity(customer_id, name=name, phone=phone, email=email, address=address),
        )
