from __future__ import annotations

from typing import Any

from fraudMCP.app.container import Container

from .common import tool_response


def register_blacklist_tools(mcp: Any, container: Container) -> None:
    source = "fraud_engine"

    @mcp.tool(
        description=(
            "Check whether an entity value appears in blacklist intelligence. Use for merchant/device/account/IP/email/phone checks when context exists."
        )
    )
    async def check_blacklist(entity_type: str, value: str) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            result = await container.blacklist_provider.check(entity_type, value)
            return {
                "entity_type": result.entity_type,
                "value": result.value,
                "matched": result.matched,
                "reason": result.reason,
                "list": result.list_name,
                "source": result.source,
                "metadata": result.metadata,
            }

        return await tool_response(customer_id=None, source=source, tool_name="check_blacklist", operation=run)
