"""Policy retrieval API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser

router = APIRouter(prefix="/api/policies", tags=["policies"])
system_router = APIRouter(prefix="/api/system", tags=["system"])


class PolicySearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/search")
async def search_policies(
    payload: PolicySearchRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> dict:
    container = request.app.state.container
    results = await container.rag_service.retrieve(payload.query, top_k=payload.top_k)
    serialized = [item.model_dump(mode="json") for item in results]
    return {"query": payload.query, "results": serialized, "citations": [
        {key: item[key] for key in ("document_id", "title", "version", "page", "section")}
        for item in serialized
    ]}


@system_router.get("/mcp/tools")
async def get_mcp_tools(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> dict:
    container = request.app.state.container
    banking, fraud, case = await container.mcp_manager.get_banking_client().list_tools(), \
        await container.mcp_manager.get_fraud_client().list_tools(), \
        await container.mcp_manager.get_case_client().list_tools()
    return {
        "banking": [item.get("name", "") for item in banking],
        "fraud": [item.get("name", "") for item in fraud],
        "case": [item.get("name", "") for item in case],
    }
