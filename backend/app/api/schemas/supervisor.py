"""Supervisor API schemas."""

from typing import Any

from pydantic import BaseModel


class SupervisorMetricsResponse(BaseModel):
    runs: dict[str, Any]
    event_counts: dict[str, int]
    waiting_hitl_count: int


class MCPToolsResponse(BaseModel):
    banking: list[str]
    fraud: list[str]
    case: list[str]
