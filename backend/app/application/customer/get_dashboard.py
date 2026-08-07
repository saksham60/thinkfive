"""Use case: get customer dashboard (parallel composition from MCPs + local data)."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.infrastructure.repositories.customer import PostgresCustomerRepository
    from app.mcp.adapters.banking import BankingMCPAdapter
    from app.mcp.adapters.case import CaseMCPAdapter
    from app.mcp.adapters.fraud import FraudMCPAdapter

logger = logging.getLogger(__name__)


class GetDashboardUseCase:
    """Composes the customer dashboard from customer_profiles + Banking/Fraud/Case MCPs."""

    def __init__(
        self,
        customer_repo: PostgresCustomerRepository,
        banking_adapter: BankingMCPAdapter,
        fraud_adapter: FraudMCPAdapter,
        case_adapter: CaseMCPAdapter,
    ) -> None:
        self.customer_repo = customer_repo
        self.banking_adapter = banking_adapter
        self.fraud_adapter = fraud_adapter
        self.case_adapter = case_adapter

    async def execute(self, customer_id: str) -> dict[str, Any]:
        profile = await self.customer_repo.get(customer_id)
        cards = await self.customer_repo.get_customer_cards(customer_id)

        # Parallel async calls to MCPs where safe
        results = await asyncio.gather(
            self.banking_adapter.get_account_summary(customer_id),
            self.banking_adapter.get_recent_transactions(customer_id, limit=10),
            self.fraud_adapter.get_fraud_alerts(customer_id),
            self.case_adapter.search_cases(customer_id=customer_id),
            return_exceptions=True,
        )

        account_summary, transactions, alerts, cases = results

        card_statuses = []
        for card in cards:
            try:
                status = await self.case_adapter.get_card_status(customer_id, card.card_id)
                card_statuses.append(status)
            except Exception as e:
                logger.warning(f"Failed to get card status for {card.card_id}: {e}")

        return {
            "profile": {
                "customer_id": profile.customer_id if profile else customer_id,
                "display_name": profile.display_name if profile else customer_id,
                "email": profile.email if profile else None,
            },
            "account_summary": account_summary if not isinstance(account_summary, Exception) else None,
            "recent_transactions": transactions if not isinstance(transactions, Exception) else None,
            "fraud_alerts": alerts if not isinstance(alerts, Exception) else None,
            "cases": cases if not isinstance(cases, Exception) else None,
            "cards": card_statuses,
        }
