"""Event publisher - persists events then broadcasts to SSE subscribers (Observer pattern)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.core.constants import EventType
from app.core.correlation import get_correlation_id
from app.events.broker import InProcessEventBroker
from app.infrastructure.repositories.agent_event import AgentEventRepository

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes domain events: persists to agent_events, then broadcasts via broker."""

    def __init__(self, event_repo: AgentEventRepository, broker: InProcessEventBroker) -> None:
        self.event_repo = event_repo
        self.broker = broker

    async def publish(
        self,
        conversation_id: UUID,
        event_type: EventType,
        payload: dict[str, Any],
        run_id: UUID | None = None,
        customer_id: str = "",
        agent_name: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Persist then broadcast an event. Persistence is the source of truth for replay."""
        stored: dict[str, Any] = {}
        if run_id is not None:
            stored = await self.event_repo.append(
                run_id=run_id,
                conversation_id=conversation_id,
                customer_id=customer_id,
                event_type=event_type.value,
                agent_name=agent_name,
                tool_name=tool_name,
                status=status,
                duration_ms=duration_ms,
                correlation_id=get_correlation_id(),
                payload=payload,
            )

        await self.broker.broadcast(
            conversation_id,
            {
                "event_seq": stored.get("event_seq", 0),
                "event_type": event_type.value,
                "payload": payload,
                "created_at": stored.get("created_at"),
            },
        )
