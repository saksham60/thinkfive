from __future__ import annotations

from fastmcp import Client


async def test_all_three_mcp_protocols_and_tool_catalogs(combined_app):
    async with combined_app.router.lifespan_context(combined_app):
        async with Client(combined_app.state.banking_server) as banking_client:
            banking_tools = await banking_client.list_tools()
            banking_call = await banking_client.call_tool("get_banking_connection_status", {"customer_id": "demo_customer_001"})
        async with Client(combined_app.state.fraud_server) as fraud_client:
            fraud_tools = await fraud_client.list_tools()
            fraud_call = await fraud_client.call_tool("check_blacklist", {"entity_type": "merchant", "value": "Local Market"})
        async with Client(combined_app.state.case_server) as case_client:
            case_tools = await case_client.list_tools()
            case_call = await case_client.call_tool("get_card_status", {"customer_id": "demo_customer_001", "card_id": "card_demo_001"})

    banking_names = {tool.name for tool in banking_tools}
    fraud_names = {tool.name for tool in fraud_tools}
    case_names = {tool.name for tool in case_tools}
    assert len(banking_names) == 15
    assert len(fraud_names) == 11
    assert len(case_names) == 23
    assert {"get_accounts", "get_transaction", "sync_transactions"}.issubset(banking_names)
    assert {"assess_transaction_risk", "create_fraud_alert", "explain_risk"}.issubset(fraud_names)
    assert {"create_case_from_fraud_alert", "approve_action", "freeze_card"}.issubset(case_names)
    assert banking_call.structured_content["success"] is True
    assert fraud_call.structured_content["success"] is True
    assert case_call.structured_content["success"] is True


async def test_tool_registries_are_isolated(combined_app):
    async with Client(combined_app.state.banking_server) as client:
        banking = {tool.name for tool in await client.list_tools()}
    async with Client(combined_app.state.fraud_server) as client:
        fraud = {tool.name for tool in await client.list_tools()}
    async with Client(combined_app.state.case_server) as client:
        case = {tool.name for tool in await client.list_tools()}
    assert "freeze_card" not in banking and "freeze_card" not in fraud
    assert "assess_transaction_risk" not in banking and "assess_transaction_risk" not in case
    assert "get_accounts" not in fraud and "get_accounts" not in case
