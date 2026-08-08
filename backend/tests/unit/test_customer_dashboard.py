from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.application.customer.get_dashboard import GetDashboardUseCase


async def test_dashboard_returns_mcp_data_for_the_authenticated_customer() -> None:
    customer_repo = SimpleNamespace(
        get=AsyncMock(
            return_value=SimpleNamespace(
                customer_id="demo_customer_002",
                display_name="Emma Wilson",
                email="emma@thinkfive.ai",
            )
        ),
        get_customer_cards=AsyncMock(return_value=[]),
    )
    banking = SimpleNamespace(
        get_account_summary=AsyncMock(return_value={"account_count": 4}),
        get_recent_transactions=AsyncMock(return_value=[{"transaction_id": "txn-1"}]),
    )
    fraud = SimpleNamespace(
        get_fraud_alerts=AsyncMock(return_value={"count": 0, "results": []})
    )
    case = SimpleNamespace(
        search_cases=AsyncMock(return_value=[]),
        get_card_status=AsyncMock(),
    )

    result = await GetDashboardUseCase(customer_repo, banking, fraud, case).execute(
        "demo_customer_002"
    )

    assert result["account_summary"] == {"account_count": 4}
    assert result["recent_transactions"] == [{"transaction_id": "txn-1"}]
    assert result["fraud_alerts"] == {"count": 0, "results": []}
    assert result["cases"] == []
    assert result["degraded_services"] == []
    banking.get_account_summary.assert_awaited_once_with("demo_customer_002")
    banking.get_recent_transactions.assert_awaited_once_with(
        "demo_customer_002", limit=10
    )


async def test_dashboard_identifies_degraded_mcp_dependencies() -> None:
    customer_repo = SimpleNamespace(
        get=AsyncMock(return_value=None),
        get_customer_cards=AsyncMock(return_value=[]),
    )
    banking = SimpleNamespace(
        get_account_summary=AsyncMock(side_effect=RuntimeError("banking unavailable")),
        get_recent_transactions=AsyncMock(side_effect=RuntimeError("banking unavailable")),
    )
    fraud = SimpleNamespace(
        get_fraud_alerts=AsyncMock(side_effect=RuntimeError("fraud unavailable"))
    )
    case = SimpleNamespace(
        search_cases=AsyncMock(side_effect=RuntimeError("case unavailable")),
        get_card_status=AsyncMock(),
    )

    result = await GetDashboardUseCase(customer_repo, banking, fraud, case).execute(
        "demo_customer_002"
    )

    assert result["account_summary"] is None
    assert result["recent_transactions"] is None
    assert result["fraud_alerts"] is None
    assert result["cases"] is None
    assert result["degraded_services"] == [
        "banking.account_summary",
        "banking.recent_transactions",
        "fraud.alerts",
        "case.cases",
    ]
