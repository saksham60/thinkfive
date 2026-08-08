"""Transaction processing state repository (baseline / dedupe for monitor)."""

from __future__ import annotations

from app.infrastructure.database.postgres import PostgresDatabase


class ProcessingStateRepository:
    """Repository for transaction_processing_state table."""

    def __init__(self, db: PostgresDatabase) -> None:
        self.db = db

    async def is_processed(self, customer_id: str, transaction_id: str) -> bool:
        val = await self.db.fetchval(
            "SELECT 1 FROM transaction_processing_state WHERE customer_id = $1 AND transaction_id = $2",
            customer_id,
            transaction_id,
        )
        return val is not None

    async def mark_processed(
        self,
        customer_id: str,
        transaction_id: str,
        assessment_id: str | None = None,
        alert_id: str | None = None,
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO transaction_processing_state (customer_id, transaction_id, assessment_id, alert_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (customer_id, transaction_id) DO UPDATE
                SET assessment_id = COALESCE($3, transaction_processing_state.assessment_id),
                    alert_id = COALESCE($4, transaction_processing_state.alert_id)
            """,
            customer_id,
            transaction_id,
            assessment_id,
            alert_id,
        )

    async def get_processed_ids(self, customer_id: str) -> set[str]:
        rows = await self.db.fetch(
            "SELECT transaction_id FROM transaction_processing_state WHERE customer_id = $1",
            customer_id,
        )
        return {r["transaction_id"] for r in rows}

    async def has_baseline(self, customer_id: str) -> bool:
        """Check whether the first monitoring pass has already established a baseline."""
        val = await self.db.fetchval(
            "SELECT 1 FROM transaction_monitor_state WHERE customer_id = $1",
            customer_id,
        )
        return val is not None

    async def mark_baseline_established(self, customer_id: str, *, transaction_count: int) -> None:
        await self.db.execute(
            """
            INSERT INTO transaction_monitor_state (customer_id, baseline_established_at, metadata)
            VALUES ($1, NOW(), jsonb_build_object('transaction_count', $2))
            ON CONFLICT (customer_id) DO NOTHING
            """,
            customer_id,
            transaction_count,
        )
