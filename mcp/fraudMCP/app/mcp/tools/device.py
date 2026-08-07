from __future__ import annotations

from typing import Any

from fraudMCP.app.container import Container

from .common import tool_response


def register_device_tools(mcp: Any, container: Container) -> None:
    source = "fraud_engine"

    @mcp.tool(
        description=(
            "Check known/trusted status for a customer device and whether it appears on blacklist intelligence. "
            "Use when transaction channel/device context is available."
        )
    )
    async def check_device(customer_id: str, device_id: str) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            device = await container.device_provider.check_device(customer_id, device_id)
            blacklist = await container.blacklist_provider.check("device", device_id)
            return {
                "customer_id": customer_id,
                "device_id": device_id,
                "known": device.known,
                "trusted": device.trusted,
                "blacklisted": blacklist.matched,
                "first_seen": device.first_seen.isoformat() if device.first_seen else None,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "country": device.country,
                "evidence_source": device.evidence_source,
                "blacklist_source": blacklist.source,
            }

        return await tool_response(customer_id=customer_id, source=source, tool_name="check_device", operation=run)
