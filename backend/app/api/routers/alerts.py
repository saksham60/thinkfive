"""Fraud alerts router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas.alert import AlertListResponse
from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser
from app.security.rbac import AuthorizationPolicy

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    customer_id: str | None = None,
) -> AlertListResponse:
    container = request.app.state.container

    target_customer_id = customer_id or user.customer_id
    if target_customer_id is None:
        raise HTTPException(status_code=400, detail="customer_id required")

    AuthorizationPolicy.assert_customer_access(user.role, user.customer_id, target_customer_id)

    result = await container.fraud_adapter.get_fraud_alerts(target_customer_id)
    return AlertListResponse(alerts=result.get("alerts", []) if isinstance(result, dict) else [])


@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> dict:
    container = request.app.state.container
    alert = await container.fraud_adapter.get_fraud_alert(alert_id)

    alert_customer_id = alert.get("customer_id") if isinstance(alert, dict) else None
    if alert_customer_id:
        AuthorizationPolicy.assert_customer_access(user.role, user.customer_id, alert_customer_id)

    return alert
