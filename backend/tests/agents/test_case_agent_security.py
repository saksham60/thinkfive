"""Critical security test: Case Agent toolset must never expose sensitive human-only tools."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.case.toolset import AUTONOMOUS_ALLOWED_TOOLS, FORBIDDEN_TOOLS, CaseToolset


class _FakeCaseAdapter:
    """Minimal fake to construct CaseToolset without a real MCP connection."""


class TestCaseAgentSecurityBoundary:
    def test_forbidden_tools_never_in_allowed_set(self) -> None:
        assert AUTONOMOUS_ALLOWED_TOOLS.isdisjoint(FORBIDDEN_TOOLS)

    def test_approve_action_not_in_tool_definitions(self) -> None:
        toolset = CaseToolset(_FakeCaseAdapter())  # type: ignore[arg-type]
        tool_names = {t["function"]["name"] for t in toolset.get_tool_definitions()}
        assert "approve_action" not in tool_names
        assert "reject_action" not in tool_names
        assert "freeze_card" not in tool_names
        assert "unfreeze_card" not in tool_names
        assert "block_card" not in tool_names

    @pytest.mark.parametrize("forbidden_tool", sorted(FORBIDDEN_TOOLS))
    async def test_execute_tool_raises_for_forbidden_tools(self, forbidden_tool: str) -> None:
        toolset = CaseToolset(_FakeCaseAdapter())  # type: ignore[arg-type]
        with pytest.raises(PermissionError):
            await toolset.execute_tool(forbidden_tool, {})

    def test_request_approval_is_allowed(self) -> None:
        assert "request_approval" in AUTONOMOUS_ALLOWED_TOOLS


async def test_create_case_forwards_transaction_and_assessment_references() -> None:
    adapter = _FakeCaseAdapter()
    adapter.create_case = AsyncMock(return_value={"case_id": "case-1"})  # type: ignore[attr-defined]
    toolset = CaseToolset(adapter, customer_id="demo_customer_001")  # type: ignore[arg-type]

    result = await toolset.execute_tool(
        "create_case",
        {
            "case_type": "TRANSACTION_DISPUTE",
            "title": "Customer-reported transaction",
            "description": "Customer confirmed this transaction was unauthorized.",
            "transaction_id": "txn-125",
            "assessment_id": "assessment-medium",
            "fraud_alert_id": "alert-optional",
        },
    )

    assert result == {"case_id": "case-1"}
    adapter.create_case.assert_awaited_once_with(  # type: ignore[attr-defined]
        customer_id="demo_customer_001",
        case_type="TRANSACTION_DISPUTE",
        title="Customer-reported transaction",
        description="Customer confirmed this transaction was unauthorized.",
        transaction_id="txn-125",
        assessment_id="assessment-medium",
        fraud_alert_id="alert-optional",
    )
