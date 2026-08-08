"""Customer API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class CustomerProfileResponse(BaseModel):
    customer_id: str
    display_name: str
    email: str | None = None


class DashboardResponse(BaseModel):
    profile: dict[str, Any]
    account_summary: Any = None
    recent_transactions: Any = None
    fraud_alerts: Any = None
    cases: Any = None
    cards: list[Any] = Field(default_factory=list)
    degraded_services: list[str] = Field(default_factory=list)
