from __future__ import annotations

from fastmcp import Client
from httpx import ASGITransport, AsyncClient

from case.app.main import create_case_asgi_app
from case.app.mcp import create_case_mcp


async def test_required_tool_catalog(container):
    expected = {
        "create_case",
        "create_case_from_fraud_alert",
        "get_case",
        "get_case_status",
        "search_cases",
        "update_case",
        "assign_case",
        "resolve_case",
        "close_case",
        "add_case_note",
        "get_case_history",
        "request_approval",
        "approve_action",
        "reject_action",
        "get_card_status",
        "freeze_card",
        "unfreeze_card",
        "block_card",
        "send_customer_notification",
        "send_email",
        "send_sms",
        "generate_case_summary",
        "get_audit_trail",
    }
    async with Client(create_case_mcp(container)) as client:
        tools = await client.list_tools()
    assert {tool.name for tool in tools} == expected


async def test_tool_success_and_safe_error_envelopes(container):
    async with Client(create_case_mcp(container)) as client:
        created = await client.call_tool("create_case", {"customer_id": "demo_customer_001", "case_type": "CUSTOMER_QUERY", "title": "Question"})
        missing = await client.call_tool("get_case", {"case_id": "00000000-0000-0000-0000-000000000000"})
    assert created.structured_content["success"] is True
    assert "SUPABASE_SERVICE_ROLE_KEY" not in str(created.structured_content)
    assert missing.structured_content == {
        "success": False,
        "error_code": "CASE_NOT_FOUND",
        "message": "Case was not found.",
        "retryable": False,
    }


async def test_health_and_readiness_routes(container):
    app = create_case_asgi_app(container.settings, container)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            health = await client.get("/health")
            ready = await client.get("/ready")
    assert health.status_code == 200
    assert health.json() == {"status": "healthy", "service": "case-mcp"}
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
