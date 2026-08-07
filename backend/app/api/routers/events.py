"""SSE events router."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import StreamingResponse

from app.core.constants import EventType
from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser
from app.security.rbac import AuthorizationPolicy

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
async def stream_events(
    request: Request,
    conversation_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    last_event_id: Annotated[int | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    """SSE stream for a conversation. Enforces customer isolation via RBAC."""
    container = request.app.state.container

    conversation = await container.conversation_repo.get(conversation_id)
    if conversation is not None:
        AuthorizationPolicy.assert_customer_access(user.role, user.customer_id, conversation.customer_id)

    async def event_generator():
        # Subscribe before reading persistence so an event emitted during replay
        # is queued instead of falling into the replay/live handoff gap.
        queue = await container.event_broker.subscribe(conversation_id)
        last_sent_event_id = last_event_id or 0
        try:
            yield f"event: connection.ready\ndata: {json.dumps({'conversation_id': str(conversation_id)})}\n\n"

            # A fresh EventSource has no cursor. Replay the newest persisted
            # events so completions emitted before the stream attached are not
            # lost. Reconnects continue from their Last-Event-ID cursor.
            if last_event_id is None:
                replayed = await container.event_replay_service.replay_recent(conversation_id)
            else:
                replayed = await container.event_replay_service.replay_since(conversation_id, last_event_id)
            for evt in replayed:
                data = json.dumps({"type": evt["event_type"], "payload": evt["payload"]}, default=str)
                yield f"id: {evt['event_seq']}\nevent: {evt['event_type']}\ndata: {data}\n\n"
                last_sent_event_id = max(last_sent_event_id, int(evt["event_seq"]))

            while True:
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=container.settings.sse_heartbeat_interval
                    )
                    event_seq = int(event.get("event_seq") or 0)
                    if event_seq and event_seq <= last_sent_event_id:
                        continue
                    data = json.dumps({"type": event["event_type"], "payload": event["payload"]}, default=str)
                    yield f"id: {event_seq}\nevent: {event['event_type']}\ndata: {data}\n\n"
                    last_sent_event_id = max(last_sent_event_id, event_seq)
                except TimeoutError:
                    yield f"event: {EventType.HEARTBEAT.value}\ndata: {{}}\n\n"
                if await request.is_disconnected():
                    break
        finally:
            await container.event_broker.unsubscribe(conversation_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
