from __future__ import annotations

from fraudMCP.app.services.fraud_service import FraudService


class AnomalyService:
    def __init__(self, fraud_service: FraudService) -> None:
        self.fraud_service = fraud_service

    async def detect_transaction_anomalies(self, customer_id: str, transaction_limit: int = 100, max_results: int = 20) -> dict[str, object]:
        return await self.fraud_service.detect_transaction_anomalies(customer_id, transaction_limit=transaction_limit, max_results=max_results)
