"""Chat router - thin: validates input, calls use case, serializes output."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser
from app.security.rbac import AuthorizationPolicy

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_chat_messages(
    conversation_id: UUID,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    run_id: UUID | None = None,
) -> list[MessageResponse]:
    """Return persisted conversation messages for SSE reconciliation."""
    container = request.app.state.container
    conversation = await container.conversation_repo.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    AuthorizationPolicy.assert_customer_access(user.role, user.customer_id, conversation.customer_id)
    messages = await container.get_history_use_case.execute(conversation_id)
    responses = [
        MessageResponse(
            message_id=str(message.message_id),
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat(),
            run_id=(
                str(message.metadata["run_id"])
                if message.metadata and message.metadata.get("run_id")
                else None
            ),
        )
        for message in messages
    ]
    if run_id is not None:
        return [message for message in responses if message.run_id == str(run_id)]
    return responses


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
