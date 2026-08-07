from __future__ import annotations

from datetime import datetime

from pydantic import Field

from .common import StrictModel


class DeviceRecord(StrictModel):
    device_id: str
    trusted: bool
    first_seen: datetime
    last_seen: datetime
    country: str | None = None


class DeviceCheckResult(StrictModel):
    customer_id: str
    device_id: str
    known: bool
    trusted: bool | None = None
    blacklisted: bool = False
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    country: str | None = None
    evidence_source: str = Field(default="synthetic_demo_data")
