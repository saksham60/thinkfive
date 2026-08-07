from __future__ import annotations

from fastmcp import FastMCP

from plaidbanking.app.container import Container

from .tools import (
    register_account_tools,
    register_identity_tools,
    register_liability_tools,
    register_sandbox_tools,
    register_transaction_tools,
)


def create_banking_mcp(container: Container) -> FastMCP:
    server = FastMCP(
        name="Plaid Banking MCP",
        instructions="Safe access to Plaid banking data. This server does not score fraud, manage cases, freeze cards, or orchestrate agents.",
    )
    register_account_tools(server, container)
    register_transaction_tools(server, container)
    register_identity_tools(server, container)
    register_liability_tools(server, container)
    register_sandbox_tools(server, container)
    return server
