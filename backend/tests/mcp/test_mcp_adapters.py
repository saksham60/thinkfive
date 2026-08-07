"""MCP adapter unit tests - verify typed adapters call correct tool names (mocked client)."""

from __future__ import annotations

from unittest.mock import AsyncMock

from app.mcp.adapters.banking import BankingMCPAdapter
from app.mcp.adapters.case import CaseMCPAdapter
from app.mcp.adapters.fraud import FraudMCPAdapter


class TestBankingMCPAdapter:
    async def test_get_accounts_calls_correct_tool(self) -> None:
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {"accounts": []}
        adapter = BankingMCPAdapter(mock_client)

        await adapter.get_accounts("demo_customer_001")

        mock_client.call_tool.assert_called_once_with("get_accounts", {"customer_id": "demo_customer_001"})


class TestFraudMCPAdapter:
    async def test_assess_transaction_risk_calls_correct_tool(self) -> None:
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {"assessment_id": "a1", "risk_score": 0.1}
        adapter = FraudMCPAdapter(mock_client)

        await adapter.assess_transaction_risk("demo_customer_001", "txn_1")

        mock_client.call_tool.assert_called_once_with(
            "assess_transaction_risk", {"customer_id": "demo_customer_001", "transaction_id": "txn_1"}
        )


class TestCaseMCPAdapter:
    async def test_request_approval_calls_correct_tool(self) -> None:
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {"approval_id": "appr_1"}
        adapter = CaseMCPAdapter(mock_client)

        await adapter.request_approval("case_1", "FREEZE_CARD", {"card_id": "card_1"})

        mock_client.call_tool.assert_called_once_with(
            "request_approval",
            {
                "case_id": "case_1",
                "action_type": "FREEZE_CARD",
                "action_payload": {"card_id": "card_1"},
                "requested_by": "agent",
            },
        )

    async def test_approve_action_calls_correct_tool_with_human_actor(self) -> None:
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {"status": "APPROVED"}
        adapter = CaseMCPAdapter(mock_client)

        await adapter.approve_action("appr_1", reviewed_by="user-uuid", reviewer_role="ANALYST")

        mock_client.call_tool.assert_called_once_with(
            "approve_action",
            {"approval_id": "appr_1", "reviewed_by": "user-uuid", "reviewer_role": "ANALYST"},
        )
