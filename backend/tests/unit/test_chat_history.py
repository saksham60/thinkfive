from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.api.routers.chat import get_chat_messages
from app.domain.conversation.entities import Conversation, Message
from app.security.auth import AuthenticatedUser


async def test_chat_history_filters_persisted_assistant_message_by_run() -> None:
    conversation_id = uuid4()
    run_id = uuid4()
    user_message = Message(
        message_id=uuid4(),
        conversation_id=conversation_id,
        role="user",
        content="What is my balance?",
        created_at=datetime.now(UTC),
        metadata=None,
    )
    assistant_message = Message(
        message_id=uuid4(),
        conversation_id=conversation_id,
        role="assistant",
        content="Your balance is $500.",
        created_at=datetime.now(UTC),
        metadata={"run_id": str(run_id)},
    )
    container = SimpleNamespace(
        conversation_repo=SimpleNamespace(
            get=AsyncMock(return_value=Conversation(conversation_id, "demo_customer_001"))
        ),
        get_history_use_case=SimpleNamespace(
            execute=AsyncMock(return_value=[user_message, assistant_message])
        ),
    )
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(container=container)))
    user = AuthenticatedUser(uuid4(), "demo@thinkfive.ai", "CUSTOMER", "demo_customer_001")

    result = await get_chat_messages(conversation_id, request, user, run_id)

    assert len(result) == 1
    assert result[0].role == "assistant"
    assert result[0].content == "Your balance is $500."
    assert result[0].run_id == str(run_id)
