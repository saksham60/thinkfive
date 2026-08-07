"""Integration tests against the real deployed MCP platform.

Skipped unless RUN_INTEGRATION_TESTS=1 is set, since they require network
access to the deployed Banking/Fraud/Case MCP services.
"""

from __future__ import annotations

import os

import pytest

from app.core.config import get_settings
from app.mcp.adapters.banking import BankingMCPAdapter
from app.mcp.adapters.case import CaseMCPAdapter
from app.mcp.adapters.fraud import FraudMCPAdapter
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

    async def test_banking_representative_call(self) -> None:
        manager = MCPManager(get_settings())
        await manager.initialize()
        try:
            result = await BankingMCPAdapter(manager.get_banking_client()).get_banking_connection_status(
                os.environ.get("TEST_CUSTOMER_ID", "demo_customer_001")
            )
            assert isinstance(result, dict)
        finally:
            await manager.close_all()

    async def test_fraud_representative_call(self) -> None:
        manager = MCPManager(get_settings())
        await manager.initialize()
        try:
            result = await FraudMCPAdapter(manager.get_fraud_client()).get_fraud_alerts(
                os.environ.get("TEST_CUSTOMER_ID", "demo_customer_001"), limit=1
            )
            assert isinstance(result, dict)
        finally:
            await manager.close_all()

    async def test_case_representative_call(self) -> None:
        manager = MCPManager(get_settings())
        await manager.initialize()
        try:
            result = await CaseMCPAdapter(manager.get_case_client()).get_card_status(
                os.environ.get("TEST_CUSTOMER_ID", "demo_customer_001"),
                os.environ.get("TEST_CARD_ID", "card_demo_001"),
            )
            assert isinstance(result, dict)
        finally:
            await manager.close_all()
