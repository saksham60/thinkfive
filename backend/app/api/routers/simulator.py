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
    merchant: str | None = None


@router.post("/transaction")
async def simulate_transaction(
    payload: SimulateTransactionRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_SIMULATOR_ROLES))],
) -> dict:
    """Create a synthetic Plaid Sandbox transaction via Banking MCP - no fabricated data."""
    container = request.app.state.container

    async with container.mcp_manager.get_banking_client() as client:
        result = await client.call_tool(
            "create_sandbox_transaction",
            {"customer_id": payload.customer_id, "amount": payload.amount, "merchant": payload.merchant},
        )
    return result
