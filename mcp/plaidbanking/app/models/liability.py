from __future__ import annotations

from typing import Any

from .common import StrictModel


class Liabilities(StrictModel):
    capability_available: bool
    credit: tuple[dict[str, Any], ...] = ()
    mortgages: tuple[dict[str, Any], ...] = ()
    student_loans: tuple[dict[str, Any], ...] = ()
    reason: str | None = None
