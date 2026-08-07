from __future__ import annotations

import os

import pytest

from fraudMCP.app.providers.banking import McpBankingDataProvider

RUN_INTEGRATION = os.getenv("RUN_BANKING_MCP_INTEGRATION_TESTS", "false").strip().casefold() == "true"


@pytest.mark.asyncio()
@pytest.mark.skipif(not RUN_INTEGRATION, reason="Set RUN_BANKING_MCP_INTEGRATION_TESTS=true to enable real Banking MCP integration tests")
async def test_mcp_banking_data_provider_against_running_banking_mcp() -> None:
    banking_url = os.getenv("BANKING_MCP_URL")
    if not banking_url:
        pytest.skip("BANKING_MCP_URL is required for integration test")

    provider = McpBankingDataProvider(
        banking_url,
        auth_token=os.getenv("BANKING_MCP_AUTH_TOKEN") or None,
        timeout_seconds=float(os.getenv("BANKING_PROVIDER_TIMEOUT_SECONDS", "10")),
        max_retries=int(os.getenv("BANKING_PROVIDER_MAX_RETRIES", "2")),
        max_backoff_seconds=float(os.getenv("BANKING_PROVIDER_MAX_BACKOFF_SECONDS", "2")),
    )

    customer_id = os.getenv("PLAID_DEFAULT_CUSTOMER_ID", "demo_customer_001")
    accounts = await provider.get_accounts(customer_id)
    assert isinstance(accounts, list)

    account_summary = await provider.get_account_summary(customer_id)
    assert isinstance(account_summary, dict)
    assert "account_count" in account_summary

    transactions = await provider.list_recent_transactions(customer_id, limit=20)
    assert isinstance(transactions, list)

    if transactions:
        txn_id = str(transactions[0].get("transaction_id") or "")
        if txn_id:
            transaction = await provider.get_transaction(customer_id, txn_id)
            assert str(transaction.get("transaction_id")) == txn_id
