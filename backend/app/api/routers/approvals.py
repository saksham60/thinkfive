"""Approval router - the only entry point for human HITL decisions.

Never trusts client-supplied reviewed_by/role/card_id/action_type fields.
Actor identity comes from the authenticated session; action payload comes
from trusted Case MCP approval state.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas.approval import ApprovalActionResponse, ApproveRequest, RejectRequest
from app.core.constants import Role
from app.dependencies import require_role
from app.security.auth import AuthenticatedUser

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

_APPROVER_ROLES = (Role.ANALYST.value, Role.SUPERVISOR.value, Role.ADMIN.value)


@router.get("/pending")
async def list_pending_approvals(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_APPROVER_ROLES))],
) -> dict:
    container = request.app.state.container
    waiting = await container.hitl_coordinator.list_waiting()
    return {"pending": [w.__dict__ for w in waiting]}


@router.post("/{approval_id}/approve", response_model=ApprovalActionResponse)
async def approve_action(
    approval_id: str,
    payload: ApproveRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_APPROVER_ROLES))],
) -> ApprovalActionResponse:
    container = request.app.state.container
    interrupt = await container.hitl_coordinator.find_waiting_by_approval(approval_id)
    if interrupt is None or not interrupt.customer_id:
        raise HTTPException(status_code=404, detail=f"No waiting workflow found for approval_id={approval_id}")
    runtime_context = container.build_runtime_context_for_resume(interrupt.customer_id)

    try:
        result = await container.approve_action_use_case.execute(
            approval_id=approval_id,
            actor_user_id=user.user_id,
            actor_role=user.role,
            runtime_context=runtime_context,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ApprovalActionResponse(approval_id=approval_id, decision="APPROVED", action_result=result)


@router.post("/{approval_id}/reject", response_model=ApprovalActionResponse)
async def reject_action(
    approval_id: str,
    payload: RejectRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_APPROVER_ROLES))],
) -> ApprovalActionResponse:
    container = request.app.state.container
    interrupt = await container.hitl_coordinator.find_waiting_by_approval(approval_id)
    if interrupt is None or not interrupt.customer_id:
        raise HTTPException(status_code=404, detail=f"No waiting workflow found for approval_id={approval_id}")
    runtime_context = container.build_runtime_context_for_resume(interrupt.customer_id)

    try:
        result = await container.reject_action_use_case.execute(
            approval_id=approval_id,
            actor_user_id=user.user_id,
            actor_role=user.role,
            runtime_context=runtime_context,
            note=payload.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ApprovalActionResponse(approval_id=approval_id, decision="REJECTED", action_result=result)
