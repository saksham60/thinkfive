"""Case router."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas.case import AddCaseNoteRequest, CaseListResponse
from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser
from app.security.rbac import AuthorizationPolicy

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=CaseListResponse)
async def list_cases(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    customer_id: str | None = None,
) -> CaseListResponse:
    container = request.app.state.container

    target: str | None
    if customer_id:
        AuthorizationPolicy.assert_customer_access(user.role, user.customer_id, customer_id)
        target = customer_id
    else:
        if not AuthorizationPolicy.can_investigate(user.role) and user.customer_id is None:
            raise HTTPException(status_code=400, detail="customer_id required")
        target = user.customer_id

    result = await container.case_adapter.search_cases(customer_id=target)
    cases: list[dict[str, Any]] = []
    if isinstance(result, list):
        cases = result
    elif isinstance(result, dict):
        candidate = result.get("cases", result.get("results", []))
        if isinstance(candidate, list):
            cases = candidate

    return CaseListResponse(cases=cases)


@router.get("/{case_id}")
async def get_case(
    case_id: str,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> dict:
    container = request.app.state.container
    case = await container.case_adapter.get_case(case_id)

    case_customer_id = case.get("customer_id") if isinstance(case, dict) else None
    if case_customer_id:
        AuthorizationPolicy.assert_customer_access(user.role, user.customer_id, case_customer_id)

    return case


@router.post("/{case_id}/notes")
async def add_case_note(
    case_id: str,
    payload: AddCaseNoteRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> dict:
    """Only analysts+ may add investigation notes through this endpoint."""
    if not AuthorizationPolicy.can_investigate(user.role):
        raise HTTPException(status_code=403, detail="Requires ANALYST role or higher")

    container = request.app.state.container
    return await container.case_adapter.add_case_note(
        case_id=case_id,
        content=payload.content,
        note_type=payload.note_type,
        author_type="HUMAN",
        author_id=str(user.user_id),
    )
