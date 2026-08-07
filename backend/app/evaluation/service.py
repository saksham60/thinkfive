"""Evaluation service facade."""

from __future__ import annotations

from typing import Any

from app.evaluation.runner import EvaluationRunner

_CATEGORIES = [
    "routing",
    "memory",
    "hitl",
    "banking_grounding",
    "fraud_grounding",
    "rag_grounding",
    "PII",
    "prompt_injection",
    "authorization",
    "provider_failure",
    "hallucination",
    "latency",
]


class EvaluationService:
    """Runs the full evaluation suite across all golden test categories."""

    def __init__(self, runner: EvaluationRunner) -> None:
        self.runner = runner

    async def run_all(self) -> dict[str, Any]:
        results = {}
        for category in _CATEGORIES:
            results[category] = await self.runner.run_category(category)
        return results
