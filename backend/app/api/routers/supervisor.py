"""Supervisor observability router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.schemas.supervisor import SupervisorMetricsResponse
from app.core.constants import Role
from app.dependencies import require_role
from app.security.auth import AuthenticatedUser

router = APIRouter(prefix="/api/supervisor", tags=["supervisor"])

_SUPERVISOR_ROLES = (Role.SUPERVISOR.value, Role.ADMIN.value)


@router.get("/metrics", response_model=SupervisorMetricsResponse)
async def get_metrics(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_SUPERVISOR_ROLES))],
) -> SupervisorMetricsResponse:
    container = request.app.state.container
    metrics = await container.supervisor_metrics_use_case.execute()
    return SupervisorMetricsResponse(**metrics)


@router.get("/runs")
async def list_runs(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_SUPERVISOR_ROLES))],
    limit: int = 100,
) -> dict:
    container = request.app.state.container
    runs = await container.agent_run_repo.list_recent(limit)
    return {"runs": runs}


@router.get("/runs/{run_id}/traces")
async def get_run_traces(
    run_id: str,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_role(*_SUPERVISOR_ROLES))],
) -> dict:
    from uuid import UUID

    container = request.app.state.container
    traces = await container.get_traces_use_case.execute(UUID(run_id))
    return {"traces": traces}
