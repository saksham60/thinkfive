from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agents.banking.toolset import BankingToolset
from app.agents.tool_loop import run_grounded_tool_loop
from app.core.config import Settings
from app.core.exceptions import MCPError
from app.mcp.adapters.case import CaseMCPAdapter
from app.mcp.adapters.fraud import FraudMCPAdapter
from app.mcp.protocol import MCPClient


def test_database_url_and_mcp_base_url_are_direct() -> None:
    settings = Settings.model_validate(
        {
            "DATABASE_URL": "postgresql://user:pass@db.example/test",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_SECRET_KEY": "secret",
            "SUPABASE_SERVICE_ROLE_KEY": "role",
            "SUPABASE_PUBLISHABLE_KEY": "public",
            "LITELLM_BASE_URL": "https://litellm.example",
            "LITELLM_API_KEY": "key",
            "MCP_BASE_URL": "https://mcp.example/",
            "MCP_AUTH_TOKEN": "token",
            "CORS_ALLOWED_ORIGINS": "http://localhost:5173, https://thinkfive.vercel.app",
            "debug": False,
        }
    )
    assert settings.database_url == "postgresql://user:pass@db.example/test"
    assert settings.banking_mcp_url == "https://mcp.example/mcp/banking"
    assert settings.fraud_mcp_url == "https://mcp.example/mcp/fraud"
    assert settings.case_mcp_url == "https://mcp.example/mcp/case"
    assert settings.cors_origins == ["http://localhost:5173", "https://thinkfive.vercel.app"]
    assert "*" not in settings.cors_origins


@pytest.mark.parametrize(
    "configured_url",
    [
        "https://mcp.example/mcp/banking",
        "https://mcp.example/mcp/banking/",
        "https://mcp.example/mcp/banking///",
    ],
)
def test_mcp_client_uses_direct_trailing_slash_url(configured_url: str) -> None:
    with patch("app.mcp.protocol.Client") as client_factory:
        client = MCPClient(configured_url, "token")

    assert client.base_url == "https://mcp.example/mcp/banking/"
    client_factory.assert_called_once_with(
        "https://mcp.example/mcp/banking/", auth="token"
    )


def test_mcp_envelope_unwraps_business_data() -> None:
    assert MCPClient._normalize_envelope("get_accounts", {"success": True, "data": {"accounts": []}}) == {
        "accounts": []
    }


def test_mcp_failure_envelope_raises_typed_error() -> None:
    with pytest.raises(MCPError) as raised:
        MCPClient._normalize_envelope(
            "create_fraud_alert",
            {"success": False, "error_code": "ASSESSMENT_BELOW_ALERT_THRESHOLD", "message": "No alert", "retryable": False},
        )
    assert raised.value.code == "ASSESSMENT_BELOW_ALERT_THRESHOLD"
    assert raised.value.retryable is False


async def test_mcp_client_reconnects_once_after_upstream_session_404() -> None:
    stale_client = MagicMock()
    stale_client.__aenter__ = AsyncMock(return_value=stale_client)
    stale_client.__aexit__ = AsyncMock()
    stale_client.ping = AsyncMock()
    stale_client.call_tool = AsyncMock(side_effect=RuntimeError("Client error '404 Not Found'"))

    replacement_client = MagicMock()
    replacement_client.__aenter__ = AsyncMock(return_value=replacement_client)
    replacement_client.__aexit__ = AsyncMock()
    replacement_client.ping = AsyncMock()
    replacement_client.call_tool = AsyncMock(
        return_value=SimpleNamespace(
            is_error=False,
            data={"success": True, "data": {"accounts": [{"account_id": "account-1"}]}},
        )
    )

    with patch(
        "app.mcp.protocol.Client", side_effect=[stale_client, replacement_client]
    ) as client_factory:
        client = MCPClient("https://mcp.example/mcp/banking", "token")
        await client.initialize()
        result = await client.call_tool("get_accounts", {"customer_id": "customer-1"})

    assert result == {"accounts": [{"account_id": "account-1"}]}
    assert client.initialized is True
    assert client_factory.call_count == 2
    stale_client.__aexit__.assert_awaited_once()
    replacement_client.ping.assert_awaited_once()
    replacement_client.call_tool.assert_awaited_once_with(
        "get_accounts", {"customer_id": "customer-1"}, timeout=60.0
    )


async def test_mcp_client_does_not_reconnect_for_non_session_failures() -> None:
    transport = MagicMock()
    transport.__aenter__ = AsyncMock(return_value=transport)
    transport.__aexit__ = AsyncMock()
    transport.ping = AsyncMock()
    transport.call_tool = AsyncMock(side_effect=RuntimeError("401 Unauthorized"))

    with patch("app.mcp.protocol.Client", return_value=transport) as client_factory:
        client = MCPClient("https://mcp.example/mcp/banking", "wrong-token")
        await client.initialize()
        with pytest.raises(MCPError, match="401 Unauthorized"):
            await client.call_tool("get_accounts", {"customer_id": "customer-1"})

    client_factory.assert_called_once()


async def test_corrected_fraud_and_case_contract_arguments() -> None:
    client = AsyncMock()
    fraud = FraudMCPAdapter(client)
    await fraud.detect_transaction_anomalies("cust", 50, 7)
    client.call_tool.assert_awaited_with(
        "detect_transaction_anomalies", {"customer_id": "cust", "transaction_limit": 50, "max_results": 7}
    )
    await fraud.check_blacklist("merchant", "bad-shop")
    client.call_tool.assert_awaited_with("check_blacklist", {"entity_type": "merchant", "value": "bad-shop"})
    await fraud.create_fraud_alert("assessment-1", "cust")
    client.call_tool.assert_awaited_with("create_fraud_alert", {"assessment_id": "assessment-1", "customer_id": "cust"})

    case = CaseMCPAdapter(client)
    await case.create_case_from_fraud_alert("alert-1")
    client.call_tool.assert_awaited_with("create_case_from_fraud_alert", {"fraud_alert_id": "alert-1"})
    await case.send_customer_notification("case-1", "EMAIL", "Content", "Subject")
    client.call_tool.assert_awaited_with(
        "send_customer_notification",
        {"case_id": "case-1", "channel": "EMAIL", "content": "Content", "subject": "Subject"},
    )


async def test_grounded_loop_returns_tool_message_to_model() -> None:
    tool_llm = AsyncMock()
    tool_llm.ainvoke.side_effect = [
        AIMessage(content="", tool_calls=[{"name": "get_accounts", "args": {}, "id": "call-1"}]),
        AIMessage(content="I used the returned accounts."),
    ]
    output_llm = AsyncMock()
    output_llm.ainvoke.return_value = {"goal_completed": True}
    toolset = AsyncMock()
    toolset.execute_tool.return_value = {"accounts": [{"account_id": "real-1", "balance": 10}]}

    result = await run_grounded_tool_loop(
        tool_llm, output_llm, toolset, [HumanMessage(content="balance?")]
    )

    second_transcript = tool_llm.ainvoke.await_args_list[1].args[0]
    assert any(isinstance(message, ToolMessage) and "real-1" in message.content for message in second_transcript)
    assert tool_llm.ainvoke.await_args_list[0].kwargs["config"]["run_name"] == "agent.specialist.tool_selection"
    assert output_llm.ainvoke.await_args.kwargs["config"]["run_name"] == "agent.specialist.structured_output"
    output_transcript = output_llm.ainvoke.await_args.args[0]
    assert isinstance(output_transcript[-1], HumanMessage)
    assert "structured output" in output_transcript[-1].content
    assert result.tool_results[0]["data"]["accounts"][0]["account_id"] == "real-1"


async def test_llm_cannot_override_trusted_customer_id() -> None:
    adapter = AsyncMock()
    toolset = BankingToolset(adapter, "trusted-customer")
    definitions = toolset.get_tool_definitions()
    assert all("customer_id" not in item["function"]["parameters"].get("properties", {}) for item in definitions)

    await toolset.execute_tool("get_accounts", {"customer_id": "attacker-customer"})
    adapter.get_accounts.assert_awaited_once_with("trusted-customer")
