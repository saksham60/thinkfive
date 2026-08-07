from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Sequence
from typing import Protocol

from fraudMCP.app.errors import AssessmentNotFoundError
from fraudMCP.app.models.assessment import RiskAssessment


class AssessmentRepository(Protocol):
    async def create_assessment(self, assessment: RiskAssessment) -> RiskAssessment: ...

    async def get_assessment(self, assessment_id: str) -> RiskAssessment: ...

    async def list_customer_assessments(self, customer_id: str, limit: int = 100) -> tuple[RiskAssessment, ...]: ...

    async def get_latest_assessment_for_transaction(self, customer_id: str, transaction_id: str) -> RiskAssessment | None: ...

    async def count_customer_assessments(self, customer_id: str) -> int: ...


class InMemoryAssessmentRepository(AssessmentRepository):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._assessments: dict[str, RiskAssessment] = {}
        self._customer_index: dict[str, list[str]] = defaultdict(list)
        self._transaction_index: dict[tuple[str, str], str] = {}

    async def create_assessment(self, assessment: RiskAssessment) -> RiskAssessment:
        async with self._lock:
            self._assessments[assessment.assessment_id] = assessment
            self._customer_index[assessment.customer_id].append(assessment.assessment_id)
            self._transaction_index[(assessment.customer_id, assessment.transaction_id)] = assessment.assessment_id
        return assessment

    async def get_assessment(self, assessment_id: str) -> RiskAssessment:
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise AssessmentNotFoundError("Risk assessment was not found.")
        return assessment

    async def list_customer_assessments(self, customer_id: str, limit: int = 100) -> tuple[RiskAssessment, ...]:
        bounded = max(1, min(limit, 200))
        ids = self._customer_index.get(customer_id, [])
        selected = ids[-bounded:]
        assessments = [self._assessments[item_id] for item_id in reversed(selected)]
        return tuple(assessments)

    async def get_latest_assessment_for_transaction(self, customer_id: str, transaction_id: str) -> RiskAssessment | None:
        assessment_id = self._transaction_index.get((customer_id, transaction_id))
        if not assessment_id:
            return None
        return self._assessments.get(assessment_id)

    async def count_customer_assessments(self, customer_id: str) -> int:
        ids: Sequence[str] = self._customer_index.get(customer_id, [])
        return len(ids)
