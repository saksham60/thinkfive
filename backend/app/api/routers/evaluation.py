"""Evaluation router - ADMIN/SUPERVISOR only."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.constants import Role
from app.dependencies import require_role
from app.security.auth import AuthenticatedUser

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

_ADMIN_ROLES = (Role.SUPERVISOR.value, Role.ADMIN.value)


@router.post("/run")
async def run_evaluation(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_ADMIN_ROLES))],
) -> dict:
    container = request.app.state.container
    result = await container.evaluation_service.run_all()
    return result
