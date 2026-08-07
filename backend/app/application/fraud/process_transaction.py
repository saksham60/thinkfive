"""Use case: process a single detected transaction through fraud assessment."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from app.core.constants import EventType
from app.core.exceptions import MCPError

if TYPE_CHECKING:
    from app.events.publisher import EventPublisher
    from app.infrastructure.repositories.processing import ProcessingStateRepository
    from app.mcp.adapters.fraud import FraudMCPAdapter

logger = logging.getLogger(__name__)

class ProcessTransactionUseCase:
    """Assesses a single transaction and creates a fraud alert if warranted.

    Never freezes cards - monitoring only creates evidence and alerts.
    """

    def __init__(
        self,
        fraud_adapter: FraudMCPAdapter,
        processing_repo: ProcessingStateRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self.fraud_adapter = fraud_adapter
        self.processing_repo = processing_repo
        self.event_publisher = event_publisher

    async def execute(self, customer_id: str, transaction_id: str, conversation_id: Any = None) -> dict[str, Any] | None:
        if await self.processing_repo.is_processed(customer_id, transaction_id):
            return None

        assessment = await self.fraud_adapter.assess_transaction_risk(customer_id, transaction_id)
        alert_id = None
        try:
            alert = await self.fraud_adapter.create_fraud_alert(
                assessment_id=assessment["assessment_id"],
                customer_id=customer_id,
            )
            alert_id = alert.get("alert_id")
        except MCPError as exc:
            if exc.code != "ASSESSMENT_BELOW_ALERT_THRESHOLD":
                raise
            logger.info("Assessment %s is a valid no-alert outcome", assessment["assessment_id"])

        await self.processing_repo.mark_processed(
            customer_id, transaction_id, assessment_id=assessment.get("assessment_id"), alert_id=alert_id
        )

        if conversation_id:
            await self.event_publisher.publish(
                conversation_id,
                EventType.TRANSACTION_ASSESSED,
                {"transaction_id": transaction_id, "risk_score": assessment.get("risk_score")},
                customer_id=customer_id,
            )
            if alert_id:
                await self.event_publisher.publish(
                    conversation_id,
                    EventType.FRAUD_ALERT_CREATED,
                    {"alert_id": alert_id, "transaction_id": transaction_id},
                    customer_id=customer_id,
                )

        return {"assessment": assessment, "alert_id": alert_id}
