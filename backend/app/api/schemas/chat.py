"""Chat API schemas."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    transaction_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    run_id: str
    status: str


class MessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    created_at: str
