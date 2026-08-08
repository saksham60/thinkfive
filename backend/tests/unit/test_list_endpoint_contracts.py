from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers import alerts, cases
from app.core.constants import Role
from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser


def _supervisor_app(*, fraud_adapter: object, case_adapter: object) -> FastAPI:
    app = FastAPI()
    app.include_router(alerts.router)
    app.include_router(cases.router)
    app.state.container = SimpleNamespace(
        fraud_adapter=fraud_adapter,
        case_adapter=case_adapter,
    )
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        uuid4(), "supervisor@thinkfive.ai", Role.SUPERVISOR.value, None
    )
    return app


def test_alert_list_accepts_fraud_mcp_results_shape() -> None:
    fraud_adapter = SimpleNamespace(
        get_fraud_alerts=AsyncMock(
            return_value={
                "count": 1,
                "results": [
                    {
                        "alert_id": "alert-1",
                        "customer_id": "demo_customer_001",
                    }
                ],
            }
        )
    )
    app = _supervisor_app(
        fraud_adapter=fraud_adapter,
        case_adapter=SimpleNamespace(search_cases=AsyncMock(return_value=[])),
    )

    response = TestClient(app).get(
        "/api/alerts", params={"customer_id": "demo_customer_001"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "alerts": [
            {
                "alert_id": "alert-1",
                "customer_id": "demo_customer_001",
            }
        ]
    }
    fraud_adapter.get_fraud_alerts.assert_awaited_once_with("demo_customer_001")


def test_case_list_accepts_case_mcp_list_shape() -> None:
    case_adapter = SimpleNamespace(
        search_cases=AsyncMock(
            return_value=[
                {
                    "case_id": "case-1",
                    "customer_id": "demo_customer_001",
                },
                {
                    "case_id": "case-2",
                    "customer_id": "demo_customer_001",
                },
            ]
        )
    )
    app = _supervisor_app(
        fraud_adapter=SimpleNamespace(get_fraud_alerts=AsyncMock(return_value=[])),
        case_adapter=case_adapter,
    )

    response = TestClient(app).get(
        "/api/cases", params={"customer_id": "demo_customer_001"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "cases": [
            {
                "case_id": "case-1",
                "customer_id": "demo_customer_001",
            },
            {
                "case_id": "case-2",
                "customer_id": "demo_customer_001",
            },
        ]
    }
    case_adapter.search_cases.assert_awaited_once_with(customer_id="demo_customer_001")
