"""Simulator router - ADMIN/SUPERVISOR only. Uses real Banking MCP Sandbox tools."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.constants import Role
from app.dependencies import require_role
from app.security.auth import AuthenticatedUser

router = APIRouter(prefix="/api/simulator", tags=["simulator"])

_SIMULATOR_ROLES = (Role.SUPERVISOR.value, Role.ADMIN.value)


class SimulateTransactionRequest(BaseModel):
    customer_id: str
    amount: float
    description: str


@router.post("/transaction")
async def simulate_transaction(
    payload: SimulateTransactionRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_SIMULATOR_ROLES))],
) -> dict:
    """Create a synthetic Plaid Sandbox transaction via Banking MCP - no fabricated data."""
    container = request.app.state.container

    return await container.simulate_transaction_use_case.execute(
        payload.customer_id, payload.amount, payload.description
    )
