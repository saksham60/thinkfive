"""Customer router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas.customer import CustomerProfileResponse, DashboardResponse
from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/me", response_model=CustomerProfileResponse)
async def get_my_profile(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> CustomerProfileResponse:
    if user.customer_id is None:
        raise HTTPException(status_code=400, detail="No associated customer account")

    container = request.app.state.container
    profile = await container.get_profile_use_case.execute(user.customer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Customer profile not found")

    return CustomerProfileResponse(
        customer_id=profile.customer_id, display_name=profile.display_name, email=profile.email
    )


@router.get("/me/dashboard", response_model=DashboardResponse)
async def get_my_dashboard(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> DashboardResponse:
    if user.customer_id is None:
        raise HTTPException(status_code=400, detail="No associated customer account")

    container = request.app.state.container
    dashboard = await container.get_dashboard_use_case.execute(user.customer_id)
    return DashboardResponse(**dashboard)
