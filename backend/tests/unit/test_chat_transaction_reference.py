from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.agents.graph.runner import GraphRunner
from app.api.routers.chat import submit_chat
from app.api.schemas.chat import ChatRequest
from app.application.conversation.submit_message import SubmitMessageUseCase
from app.domain.conversation.entities import Conversation
from app.security.auth import AuthenticatedUser


@pytest.mark.parametrize("transaction_id", ["txn-123", None])
async def test_chat_api_propagates_optional_transaction_reference(transaction_id: str | None) -> None:
    conversation_id = uuid4()
    run_id = uuid4()
    execute = AsyncMock(
        return_value={
            "conversation_id": str(conversation_id),
            "run_id": str(run_id),
            "status": "QUEUED",
        }
    )
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                container=SimpleNamespace(
                    submit_message_use_case=SimpleNamespace(execute=execute)
                )
            )
        )
    )
    user = AuthenticatedUser(uuid4(), "demo@thinkfive.ai", "CUSTOMER", "demo_customer_001")

    response = await submit_chat(
        ChatRequest(message="Check this transaction", transaction_id=transaction_id),
        request,
        user,
    )

    assert response.status == "QUEUED"
    execute.assert_awaited_once_with(
        customer_id="demo_customer_001",
        message="Check this transaction",
        conversation_id=None,
        transaction_id=transaction_id,
    )


@pytest.mark.parametrize("transaction_id", ["txn-123", None])
async def test_submit_message_passes_reference_to_graph_runner(transaction_id: str | None) -> None:
    conversation_id = uuid4()
    run_id = uuid4()
    conversation = Conversation(conversation_id, "demo_customer_001")
    conversation_repo = SimpleNamespace(
        create=AsyncMock(return_value=conversation),
        add_message=AsyncMock(side_effect=lambda message: message),
        get_messages=AsyncMock(return_value=[]),
    )
    graph_runner = SimpleNamespace(
        start_run=AsyncMock(),
        recent_message_limit=10,
        summary_threshold=20,
    )
    memory_service = SimpleNamespace(
        process_user_message=AsyncMock(),
        maybe_summarize=AsyncMock(return_value=None),
        memory_repo=SimpleNamespace(get_summary=AsyncMock(return_value=None)),
        get_memory_context=AsyncMock(return_value={}),
    )
    use_case = SubmitMessageUseCase(
        conversation_repo,
        SimpleNamespace(create=AsyncMock(return_value=run_id)),
        graph_runner,
        SimpleNamespace(publish=AsyncMock()),
        memory_service,
        lambda customer_id: {"trusted_customer_id": customer_id},
    )

    await use_case.execute(
        "demo_customer_001",
        "Check this transaction",
        transaction_id=transaction_id,
    )
    await asyncio.sleep(0)

    assert graph_runner.start_run.await_args.kwargs["requested_transaction_id"] == transaction_id
    assert graph_runner.start_run.await_args.kwargs["customer_id"] == "demo_customer_001"


@pytest.mark.parametrize("transaction_id", ["txn-123", None])
async def test_graph_initial_state_keeps_reference_untrusted(transaction_id: str | None) -> None:
    captured_state: dict = {}

    async def invoke(state: dict, config: dict) -> dict:
        captured_state.update(state)
        return {"final_response": "Done"}

    graph = SimpleNamespace(
        ainvoke=AsyncMock(side_effect=invoke),
        aget_state=AsyncMock(return_value=SimpleNamespace(next=())),
    )
    conversation_repo = SimpleNamespace(
        has_assistant_message_for_run=AsyncMock(return_value=False),
        add_message=AsyncMock(),
        get_messages=AsyncMock(return_value=[]),
    )
    runner = GraphRunner(
        graph,
        SimpleNamespace(update_status=AsyncMock()),
        SimpleNamespace(),
        SimpleNamespace(publish=AsyncMock()),
        SimpleNamespace(),
        conversation_repo,
        SimpleNamespace(maybe_summarize=AsyncMock()),
    )

    await runner.start_run(
        run_id=uuid4(),
        conversation_id=uuid4(),
        thread_id=str(uuid4()),
        customer_id="demo_customer_001",
        message="Check this transaction",
        runtime_context={},
        requested_transaction_id=transaction_id,
    )

    assert captured_state["requested_transaction_id"] == transaction_id
    assert captured_state["active_transaction_id"] is None
    assert captured_state["customer_id"] == "demo_customer_001"
