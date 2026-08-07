"""SSE event schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SSEEvent(BaseModel):
    """A single SSE event."""

    event_seq: int
    event_type: str
    conversation_id: str
    payload: dict[str, Any]
    created_at: datetime

    def to_sse_format(self) -> str:
        """Format as an SSE wire message."""
        import json

        data = json.dumps({"type": self.event_type, "payload": self.payload})
        return f"id: {self.event_seq}\nevent: {self.event_type}\ndata: {data}\n\n"
