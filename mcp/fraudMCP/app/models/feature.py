from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import StrictModel


class FeatureValue(StrictModel):
    feature: str
    available: bool
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    weight: float = Field(default=0.0, ge=0.0, le=1.0)
    contribution: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: dict[str, Any] = Field(default_factory=dict)
