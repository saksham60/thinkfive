from __future__ import annotations

import httpx
import pytest
from fastmcp import Client

from plaidbanking.app.config import Settings
from plaidbanking.app.container import create_container
from plaidbanking.app.main import create_banking_asgi_app
from plaidbanking.app.mcp import create_banking_mcp
from plaidbanking.tests.conftest import FakePlaid

EXPECTED_TOOLS = {
    "get_customer_identity",
    "verify_customer_identity",
    "get_accounts",
    "get_account_summary",
    "get_account_balance",
    "sync_transactions",
    "get_recent_transactions",
    "get_transaction",
    "search_transactions",
    "refresh_transactions",
    "get_liabilities",
    "get_banking_connection_status",
    "simulate_transaction",
    "fire_transaction_webhook",
    "create_demo_fraud_scenario",
}


@pytest.mark.asyncio
async def test_all_tool_contracts_are_registered(container) -> None:
    server = create_banking_mcp(container)
    async with Client(server) as client:
        tools = await client.list_tools()
    assert {tool.name for tool in tools} == EXPECTED_TOOLS


@pytest.mark.asyncio
async def test_tool_failure_is_safe_and_structured(container) -> None:
    server = create_banking_mcp(container)
    async with Client(server) as client:
        result = await client.call_tool("get_accounts", {"customer_id": "unknown"})
    structured = result.structured_content["result"] if "result" in result.structured_content else result.structured_content
    serialized = str(structured)
    assert "CUSTOMER_NOT_FOUND" in serialized
    assert "access_token" not in serialized and "test-secret" not in serialized


@pytest.mark.asyncio
async def test_health_ready_and_configurable_mount(settings: Settings, fake_plaid: FakePlaid) -> None:
    app = create_banking_asgi_app(settings, create_container(settings, fake_plaid), mount_path="/mcp/banking")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        health = await client.get("/health")
        ready = await client.get("/ready")
        mcp = await client.post("/mcp/banking", json={})
    assert health.status_code == 200 and ready.status_code == 200
    assert mcp.status_code != 404


@pytest.mark.asyncio
async def test_optional_mcp_bearer_auth(fake_plaid: FakePlaid) -> None:
    settings = Settings(_env_file=None, PLAID_CLIENT_ID="client", PLAID_SECRET="secret", PLAID_AUTO_BOOTSTRAP=False, MCP_AUTH_TOKEN="mcp-token")
    app = create_banking_asgi_app(settings, create_container(settings, fake_plaid))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            denied = await client.post("/mcp/", json={})
            allowed = await client.post("/mcp/", json={}, headers={"Authorization": "Bearer mcp-token"})
            health = await client.get("/health")
    assert denied.status_code == 401
    assert allowed.status_code != 401
    assert health.status_code == 200
