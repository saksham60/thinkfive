"""Use case: periodic transaction monitoring across watched customers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.application.fraud.process_transaction import ProcessTransactionUseCase
    from app.infrastructure.repositories.processing import ProcessingStateRepository
    from app.mcp.adapters.banking import BankingMCPAdapter

logger = logging.getLogger(__name__)


class MonitorTransactionsUseCase:
    """Checks Banking MCP recent transactions for monitored customers.

    First pass establishes a baseline (marks existing transactions as
    processed without alerting) so historical Plaid data is never treated
    as a new live fraud event.
    """

    def __init__(
        self,
        banking_adapter: BankingMCPAdapter,
        processing_repo: ProcessingStateRepository,
        process_transaction: ProcessTransactionUseCase,
    ) -> None:
        self.banking_adapter = banking_adapter
        self.processing_repo = processing_repo
        self.process_transaction = process_transaction

    async def execute(self, customer_id: str) -> dict[str, int]:
        recent = await self.banking_adapter.get_recent_transactions(customer_id, limit=50)
        transactions = self._transactions(recent)

        has_baseline = await self.processing_repo.has_baseline(customer_id)

        if not has_baseline:
            # Baseline protection: mark all existing transactions processed without alerting.
            for txn in transactions:
                txn_id = txn.get("transaction_id")
                if txn_id:
                    await self.processing_repo.mark_processed(customer_id, txn_id)
            await self.processing_repo.mark_baseline_established(customer_id, transaction_count=len(transactions))
            logger.info(f"Baseline established for {customer_id}: {len(transactions)} transactions")
            return {"baseline_established": len(transactions), "assessed": 0}

        assessed_count = 0
        for txn in transactions:
            txn_id = txn.get("transaction_id")
            if not txn_id:
                continue
            result = await self.process_transaction.execute(customer_id, txn_id)
            if result is not None:
                assessed_count += 1

        return {"baseline_established": 0, "assessed": assessed_count}

    @staticmethod
    def _transactions(response: Any) -> list[dict[str, Any]]:
        """Normalize current and legacy Banking MCP transaction response shapes."""
        values = response
        if isinstance(response, dict):
            values = response.get(
                "transactions",
                response.get("results", response.get("data", [])),
            )
            if isinstance(values, dict):
                values = values.get("transactions", values.get("results", []))
        if not isinstance(values, list):
            return []
        return [value for value in values if isinstance(value, dict)]
