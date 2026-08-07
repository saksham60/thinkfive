from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_MCP_INTEGRATION_TESTS", "false").lower() != "true",
    reason="set RUN_MCP_INTEGRATION_TESTS=true with Banking and Fraud MCP URLs",
)


async def test_cross_mcp_urls_are_configured():
    from case.app.config import Settings
    from case.app.container import create_container
    from case.app.models.domain import CardState
    from case.app.providers import McpBankingDataProvider, McpFraudDataProvider

    settings = Settings()
    assert settings.banking_mcp_url
    assert settings.fraud_mcp_url
    alert_id = os.environ["CASE_TEST_FRAUD_ALERT_ID"]
    customer_id = os.environ["CASE_TEST_CUSTOMER_ID"]
    card_id = os.getenv("CASE_TEST_CARD_ID", "card_cross_mcp_001")
    banking = McpBankingDataProvider(
        settings.banking_mcp_url,
        settings.banking_mcp_auth_token.get_secret_value() if settings.banking_mcp_auth_token else None,
    )
    fraud = McpFraudDataProvider(
        settings.fraud_mcp_url,
        settings.fraud_mcp_auth_token.get_secret_value() if settings.fraud_mcp_auth_token else None,
    )
    container = create_container(settings, memory=True, banking=banking, fraud=fraud)
    await container.cards.upsert(CardState(card_id=card_id, customer_id=customer_id))
    case = await container.case.from_alert(alert_id)
    assert case.customer_id == customer_id
    approval = await container.approval.request(case.case_id, "FREEZE_CARD", {"card_id": card_id}, "cross_mcp_agent")
    assert (await container.cards.get(card_id)).status == "ACTIVE"
    await container.approval.approve(approval.approval_id, "cross_mcp_human")
    assert (await container.cards.get(card_id)).status == "FROZEN"
