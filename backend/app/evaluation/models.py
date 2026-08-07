"""Evaluation models."""

from pydantic import BaseModel


class EvaluationCaseResult(BaseModel):
    case_id: str
    name: str
    category: str
    passed: bool
    error_message: str | None = None
    duration_ms: float | None = None
