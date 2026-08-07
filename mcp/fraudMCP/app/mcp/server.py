from __future__ import annotations

from fastmcp import FastMCP

from fraudMCP.app.container import Container

from .tools import register_alert_tools, register_anomaly_tools, register_assessment_tools, register_blacklist_tools, register_device_tools


def create_fraud_mcp(container: Container) -> FastMCP:
    server = FastMCP(
        name="Fraud MCP",
        instructions=(
            "Fraud-risk analysis MCP for banking transactions. "
            "Produces explainable risk assessments and fraud alerts from banking evidence. "
            "This server never freezes cards, blocks accounts, issues refunds, sends notifications, or creates cases."
        ),
    )
    register_assessment_tools(server, container)
    register_anomaly_tools(server, container)
    register_device_tools(server, container)
    register_blacklist_tools(server, container)
    register_alert_tools(server, container)
    return server
