from __future__ import annotations

from typing import Any

from .common import StrictModel


class BlacklistCheckResult(StrictModel):
    entity_type: str
    value: str
    matched: bool
    reason: str | None = None
    list_name: str | None = None
    source: str = "synthetic_demo_data"
    metadata: dict[str, Any] | None = None
