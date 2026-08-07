"""Integration tests against the real deployed MCP platform.

Skipped unless RUN_INTEGRATION_TESTS=1 is set, since they require network
access to the deployed Banking/Fraud/Case MCP services.
"""

from __future__ import annotations

import os

import pytest

from app.core.config import get_settings
from app.mcp.manager import MCPManager

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_INTEGRATION_TESTS") != "1",
    reason="Set RUN_INTEGRATION_TESTS=1 to run live MCP integration tests",
)


class TestMCPIntegration:
    async def test_banking_mcp_tools_list(self) -> None:
        settings = get_settings()
        manager = MCPManager(settings)
        async with manager.get_banking_client() as client:
            tools = await client.list_tools()
            assert len(tools) > 0

    async def test_fraud_mcp_tools_list(self) -> None:
        settings = get_settings()
        manager = MCPManager(settings)
        async with manager.get_fraud_client() as client:
            tools = await client.list_tools()
            assert len(tools) > 0

    async def test_case_mcp_tools_list(self) -> None:
        settings = get_settings()
        manager = MCPManager(settings)
        async with manager.get_case_client() as client:
            tools = await client.list_tools()
            assert len(tools) > 0
