"""Evaluation repository implementation."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from app.infrastructure.database.postgres import PostgresDatabase


class EvaluationRepository:
    """Repository for evaluation_cases / evaluation_runs / evaluation_results."""

    def __init__(self, db: PostgresDatabase) -> None:
        self.db = db

    async def list_cases(self, category: str | None = None) -> list[dict[str, Any]]:
        if category:
            rows = await self.db.fetch(
                "SELECT * FROM evaluation_cases WHERE is_active = TRUE AND category = $1",
                category,
            )
        else:
            rows = await self.db.fetch("SELECT * FROM evaluation_cases WHERE is_active = TRUE")
        return [dict(r) for r in rows]

    async def create_run(self, run_name: str | None = None) -> UUID:
        run_id = uuid4()
        await self.db.execute(
            "INSERT INTO evaluation_runs (run_id, run_name) VALUES ($1, $2)",
            run_id,
            run_name,
        )
        return run_id

    async def record_result(
        self,
        run_id: UUID,
        case_id: UUID,
        passed: bool,
        actual_output: dict[str, Any] | None = None,
        actual_agent: str | None = None,
        duration_ms: float | None = None,
        error_message: str | None = None,
        score: float | None = None,
    ) -> None:
        import json

        await self.db.execute(
            """
            INSERT INTO evaluation_results
                (result_id, run_id, case_id, passed, actual_output, actual_agent, duration_ms, error_message, score)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            uuid4(),
            run_id,
            case_id,
            passed,
            json.dumps(actual_output) if actual_output else None,
            actual_agent,
            duration_ms,
            error_message,
            score,
        )

    async def complete_run(
        self, run_id: UUID, total: int, passed: int, failed: int, skipped: int
    ) -> None:
        await self.db.execute(
            """
            UPDATE evaluation_runs
            SET completed_at = NOW(), total_cases = $2, passed_cases = $3,
                failed_cases = $4, skipped_cases = $5
            WHERE run_id = $1
            """,
            run_id,
            total,
            passed,
            failed,
            skipped,
        )
