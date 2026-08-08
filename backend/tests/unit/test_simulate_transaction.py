from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers import simulator
from app.application.fraud.simulate_transaction import SimulateTransactionUseCase
from app.core.constants import Role
from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser


def transaction(transaction_id: str, amount: float, description: str) -> dict:
    return {
        "transaction_id": transaction_id,
        "account_id": "account-1",
        "amount": amount,
        "transaction_name": description,
        "pending": True,
    }


def banking_adapter(*recent_responses: dict) -> Mock:
    adapter = Mock()
    adapter.attach_mock(AsyncMock(side_effect=recent_responses), "get_recent_transactions")
    adapter.attach_mock(
        AsyncMock(
            return_value={
                "accepted": True,
                "synthetic": True,
                "environment": "sandbox",
                "message": "Sandbox transaction created.",
            }
        ),
        "simulate_transaction",
    )
    adapter.attach_mock(AsyncMock(return_value={"sync_completed": True}), "sync_transactions")
    return adapter


async def test_simulator_captures_before_ids_then_syncs_and_returns_new_transaction() -> None:
    duplicate = transaction("existing-id", 2500, "International Electronics Purchase")
    created = transaction("new-plaid-id", 2500, "International Electronics Purchase")
    adapter = banking_adapter(
        {"transactions": [duplicate]},
        {"transactions": [created, duplicate]},
    )
    sleep = AsyncMock()
    use_case = SimulateTransactionUseCase(adapter, sleep=sleep)

    result = await use_case.execute(
        "demo_customer_001", 2500, "International Electronics Purchase"
    )

    assert adapter.mock_calls[:4] == [
        call.get_recent_transactions("demo_customer_001", limit=100),
        call.simulate_transaction(
            "demo_customer_001", 2500, "International Electronics Purchase"
        ),
        call.sync_transactions("demo_customer_001"),
        call.get_recent_transactions("demo_customer_001", limit=100),
    ]
    adapter.simulate_transaction.assert_awaited_once()
    adapter.sync_transactions.assert_awaited_once_with("demo_customer_001")
    sleep.assert_not_awaited()
    assert result["accepted"] is True
    assert result["synthetic"] is True
    assert result["environment"] == "sandbox"
    assert result["synchronized"] is True
    assert result["transaction"] == created
    assert result["transaction"]["transaction_id"] == "new-plaid-id"


async def test_simulator_does_not_match_duplicate_present_before_simulation() -> None:
    duplicate = transaction("existing-id", 2500, "International Electronics Purchase")
    adapter = banking_adapter(
        {"transactions": [duplicate]},
        *({"transactions": [duplicate]} for _ in range(4)),
    )
    sleep = AsyncMock()

    result = await SimulateTransactionUseCase(adapter, sleep=sleep).execute(
        "demo_customer_001", 2500, "International Electronics Purchase"
    )

    assert result["synchronized"] is False
    assert result["transaction"] is None


async def test_simulator_detects_transaction_on_a_later_bounded_attempt() -> None:
    created = transaction("delayed-id", 45.67, "Delayed Sandbox Purchase")
    adapter = banking_adapter(
        {"transactions": []},
        {"transactions": []},
        {"transactions": [created]},
    )
    sleep = AsyncMock()

    result = await SimulateTransactionUseCase(adapter, sleep=sleep).execute(
        "demo_customer_001", 45.67, "Delayed Sandbox Purchase"
    )

    assert adapter.sync_transactions.await_count == 2
    assert sleep.await_args_list == [call(1.0)]
    assert result["synchronized"] is True
    assert result["transaction"] == created


async def test_simulator_retry_is_bounded_and_never_fabricates_transaction() -> None:
    adapter = banking_adapter(
        {"transactions": []},
        *({"transactions": []} for _ in range(4)),
    )
    sleep = AsyncMock()

    result = await SimulateTransactionUseCase(adapter, sleep=sleep).execute(
        "demo_customer_001", 99.95, "Delayed Sandbox Purchase"
    )

    adapter.simulate_transaction.assert_awaited_once()
    assert adapter.sync_transactions.await_count == 4
    assert adapter.get_recent_transactions.await_count == 5
    assert sleep.await_args_list == [call(1.0), call(1.0), call(1.0)]
    assert result == {
        "accepted": True,
        "synthetic": True,
        "environment": "sandbox",
        "synchronized": False,
        "transaction": None,
        "message": (
            "Transaction was accepted by the banking provider but has not materialized "
            "in the canonical transaction store yet."
        ),
    }


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [
        (Role.CUSTOMER.value, 403),
        (Role.ANALYST.value, 403),
        (Role.SUPERVISOR.value, 200),
        (Role.ADMIN.value, 200),
    ],
)
def test_simulator_endpoint_rbac_and_no_processing_state_write(
    role: str, expected_status: int
) -> None:
    app = FastAPI()
    app.include_router(simulator.router)
    simulate_use_case = AsyncMock(
        return_value={
            "accepted": True,
            "synthetic": True,
            "environment": "sandbox",
            "synchronized": True,
            "transaction": transaction("new-id", 2500, "International Electronics Purchase"),
        }
    )
    processing_repo = SimpleNamespace(mark_processed=AsyncMock())
    app.state.container = SimpleNamespace(
        simulate_transaction_use_case=SimpleNamespace(execute=simulate_use_case),
        processing_repo=processing_repo,
    )
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        uuid4(), f"{role.lower()}@thinkfive.ai", role, None
    )

    response = TestClient(app).post(
        "/api/simulator/transaction",
        json={
            "customer_id": "demo_customer_001",
            "amount": 2500,
            "description": "International Electronics Purchase",
        },
    )

    assert response.status_code == expected_status
    if expected_status == 200:
        simulate_use_case.assert_awaited_once_with(
            "demo_customer_001", 2500.0, "International Electronics Purchase"
        )
    else:
        simulate_use_case.assert_not_awaited()
    processing_repo.mark_processed.assert_not_awaited()
