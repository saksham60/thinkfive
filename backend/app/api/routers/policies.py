"""System MCP capability discovery router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.schemas.supervisor import MCPToolsResponse
from app.core.constants import Role
from app.dependencies import require_role
from app.security.auth import AuthenticatedUser

router = APIRouter(prefix="/api/system", tags=["system"])

_SUPERVISOR_ROLES = (Role.SUPERVISOR.value, Role.ADMIN.value)


@router.get("/mcp/tools", response_model=MCPToolsResponse)
async def get_mcp_tools(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_SUPERVISOR_ROLES))],
) -> MCPToolsResponse:
    """Discover actual deployed MCP tools via tools/list - prevents catalog drift."""
    container = request.app.state.container

    async with container.mcp_manager.get_banking_client() as banking_client:
        banking_tools = await banking_client.list_tools()
    async with container.mcp_manager.get_fraud_client() as fraud_client:
        fraud_tools = await fraud_client.list_tools()
    async with container.mcp_manager.get_case_client() as case_client:
        case_tools = await case_client.list_tools()

    return MCPToolsResponse(
        banking=[t.get("name", "") for t in banking_tools],
        fraud=[t.get("name", "") for t in fraud_tools],
        case=[t.get("name", "") for t in case_tools],
    )
