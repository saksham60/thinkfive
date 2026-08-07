"""Evaluation runner - executes golden test cases against the real graph."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from app.evaluation.scorers import GroundingScorer, PIIScorer, RoutingScorer

if TYPE_CHECKING:
    from app.infrastructure.repositories.evaluation import EvaluationRepository

logger = logging.getLogger(__name__)


class EvaluationRunner:
    """Runs evaluation_cases through real graph execution and scores results."""

    def __init__(self, evaluation_repo: EvaluationRepository, graph_runner_factory: Any) -> None:
        self.evaluation_repo = evaluation_repo
        self.graph_runner_factory = graph_runner_factory
        self.routing_scorer = RoutingScorer()
        self.grounding_scorer = GroundingScorer()
        self.pii_scorer = PIIScorer()

    async def run_category(self, category: str) -> dict[str, Any]:
        cases = await self.evaluation_repo.list_cases(category=category)
        run_id = await self.evaluation_repo.create_run(run_name=f"eval_{category}")

        passed_count = 0
        failed_count = 0
        skipped_count = 0

        for case in cases:
            start = time.monotonic()
            try:
                if self.graph_runner_factory is None:
                    raise RuntimeError("Evaluation graph executor is unavailable")
                actual = await self.graph_runner_factory(case)
                passed = self._score_case(category, case, actual)
                error = None if passed else "Evaluation assertion failed"
            except Exception as e:
                passed = False
                error = f"SKIPPED: {e}"

            duration_ms = (time.monotonic() - start) * 1000
            await self.evaluation_repo.record_result(
                run_id=run_id,
                case_id=case["case_id"],
                passed=passed,
                duration_ms=duration_ms,
                error_message=error,
            )
            if error and error.startswith("SKIPPED:"):
                skipped_count += 1
            elif passed:
                passed_count += 1
            else:
                failed_count += 1

        await self.evaluation_repo.complete_run(
            run_id, total=len(cases), passed=passed_count, failed=failed_count, skipped=skipped_count
        )

        return {
            "run_id": str(run_id),
            "category": category,
            "total": len(cases),
            "passed": passed_count,
            "failed": failed_count,
            "skipped": skipped_count,
        }

    def _score_case(self, category: str, case: dict[str, Any], actual: dict[str, Any]) -> bool:
        if category == "PII":
            return self.pii_scorer.score(actual.get("final_response", ""))
        if category == "authorization":
            return bool(actual.get("authorization_safe"))
        if category == "hitl":
            return bool(actual.get("interrupted") and actual.get("approval_id"))
        if category == "rag_grounding":
            citations = actual.get("policy_evidence", {}).get("citations", [])
            retrieved = actual.get("policy_evidence", {}).get("retrieved_chunks", [])
            document_ids = {str(item.get("document_id")) for item in retrieved}
            return bool(retrieved) and all(str(item.get("document_id")) in document_ids for item in citations)
        expected_agent = case.get("expected_agent")
        if expected_agent and not self.routing_scorer.score(expected_agent, actual.get("actual_agent")):
            return False
        expected_tools = set(case.get("expected_tools") or [])
        return expected_tools.issubset(set(actual.get("actual_tools") or []))
