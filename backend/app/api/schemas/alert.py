"""Alert API schemas."""

from typing import Any

from pydantic import BaseModel


class AlertListResponse(BaseModel):
    alerts: list[dict[str, Any]]
