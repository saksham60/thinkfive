"""Event replay support (Last-Event-ID handling)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.infrastructure.repositories.agent_event import AgentEventRepository


class EventReplayService:
    """Replays persisted events for SSE reconnection using Last-Event-ID."""

    def __init__(self, event_repo: AgentEventRepository) -> None:
        self.event_repo = event_repo

    async def replay_since(self, conversation_id: UUID, last_event_id: int) -> list[dict[str, Any]]:
        """Get events after the given event_seq for replay after reconnect."""
        events = await self.event_repo.get_since(conversation_id, after_seq=last_event_id)
        return [
            {
                "event_seq": e["event_seq"],
                "event_type": e["event_type"],
                "payload": e["payload"],
                "created_at": e["created_at"],
            }
            for e in events
        ]
