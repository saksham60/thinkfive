"""Chat router - thin: validates input, calls use case, serializes output."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas.chat import ChatRequest, ChatResponse
from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def submit_chat(
    payload: ChatRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> ChatResponse:
    """Submit a chat message. Customer ID comes from the authenticated session only."""
    if user.customer_id is None:
        raise HTTPException(status_code=400, detail="User is not associated with a customer account")

    container = request.app.state.container
    conversation_id = UUID(payload.conversation_id) if payload.conversation_id else None

    result = await container.submit_message_use_case.execute(
        customer_id=user.customer_id,
        message=payload.message,
        conversation_id=conversation_id,
    )
    return ChatResponse(**result)
