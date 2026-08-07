"""SSE event broker tests - customer isolation and pub/sub semantics."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

from app.events.broker import InProcessEventBroker
from app.events.replay import EventReplayService


class TestInProcessEventBroker:
    async def test_subscriber_receives_broadcast_event(self) -> None:
        broker = InProcessEventBroker()
        conversation_id = uuid4()
        queue = await broker.subscribe(conversation_id)

        await broker.broadcast(conversation_id, {"event_type": "test.event", "payload": {}})

        event = await asyncio.wait_for(queue.get(), timeout=1)
        assert event["event_type"] == "test.event"

    async def test_conversation_isolation(self) -> None:
        """Events for conversation A must never reach a subscriber of conversation B."""
        broker = InProcessEventBroker()
        conv_a, conv_b = uuid4(), uuid4()

        queue_a = await broker.subscribe(conv_a)
        queue_b = await broker.subscribe(conv_b)

        await broker.broadcast(conv_a, {"event_type": "a.event", "payload": {}})

        event = await asyncio.wait_for(queue_a.get(), timeout=1)
        assert event["event_type"] == "a.event"
        assert queue_b.empty()

    async def test_unsubscribe_stops_delivery(self) -> None:
        broker = InProcessEventBroker()
        conversation_id = uuid4()
        queue = await broker.subscribe(conversation_id)
        await broker.unsubscribe(conversation_id, queue)

        await broker.broadcast(conversation_id, {"event_type": "test.event", "payload": {}})
        assert queue.empty()


async def test_replay_decodes_persisted_json_payload() -> None:
    repo = AsyncMock()
    repo.get_since.return_value = [{
        "event_seq": 4, "event_type": "workflow.resumed",
        "payload": '{"run_id":"run-1"}', "created_at": None,
    }]
    result = await EventReplayService(repo).replay_since(uuid4(), 3)
    assert result[0]["payload"] == {"run_id": "run-1"}


async def test_fresh_stream_replays_recent_persisted_events() -> None:
    repo = AsyncMock()
    repo.get_recent.return_value = [{
        "event_seq": 9, "event_type": "chat.completed",
        "payload": '{"run_id":"run-1","response":"Balance is $10"}', "created_at": None,
    }]

    result = await EventReplayService(repo).replay_recent(uuid4())

    repo.get_recent.assert_awaited_once()
    assert result == [{
        "event_seq": 9,
        "event_type": "chat.completed",
        "payload": {"run_id": "run-1", "response": "Balance is $10"},
        "created_at": None,
    }]
