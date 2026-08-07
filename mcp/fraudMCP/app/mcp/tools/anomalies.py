from __future__ import annotations

from typing import Any

from fraudMCP.app.container import Container

from .common import tool_response


def register_anomaly_tools(mcp: Any, container: Container) -> None:
    source = "fraud_engine"

    @mcp.tool(
        description=(
            "Score recent customer transactions for anomaly risk and return the highest-risk subset. "
            "Use for proactive fraud monitoring or supervisor dashboard triage. "
            "This tool does not create cases."
        )
    )
    async def detect_transaction_anomalies(customer_id: str, transaction_limit: int = 100, max_results: int = 20) -> dict[str, Any]:
        async def run(_: str) -> dict[str, Any]:
            return await container.anomaly_service.detect_transaction_anomalies(
                customer_id,
                transaction_limit=transaction_limit,
                max_results=max_results,
            )

        return await tool_response(customer_id=customer_id, source=source, tool_name="detect_transaction_anomalies", operation=run)
