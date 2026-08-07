from __future__ import annotations

from datetime import date

from plaidbanking.app.config import Settings
from plaidbanking.app.plaid.client import PlaidGateway
from plaidbanking.app.plaid.exceptions import CustomerNotFoundError, InvalidInputError
from plaidbanking.app.repositories.item_repository import ItemNotFoundError, ItemRepository
from plaidbanking.app.repositories.sync_state_repository import SyncStateRepository


class SandboxService:
    def __init__(self, settings: Settings, plaid: PlaidGateway, items: ItemRepository, sync_states: SyncStateRepository) -> None:
        self.settings = settings
        self.plaid = plaid
        self.items = items
        self.sync_states = sync_states

    def _require_sandbox(self) -> None:
        if self.settings.plaid_env != "sandbox":
            raise InvalidInputError("Sandbox mutation tools are disabled outside the Plaid Sandbox.")

    async def _token(self, customer_id: str) -> str:
        try:
            return await self.items.get_access_token(customer_id)
        except ItemNotFoundError:
            raise CustomerNotFoundError("No banking connection exists for this customer.") from None

    async def simulate_transaction(self, customer_id: str, amount: float, description: str, transaction_date: date | None = None) -> dict[str, object]:
        self._require_sandbox()
        if amount == 0 or not description.strip():
            raise InvalidInputError("A non-zero amount and description are required.")
        await self.plaid.create_sandbox_transaction(
            await self._token(customer_id), amount, description.strip(), transaction_date.isoformat() if transaction_date else None
        )
        await self.sync_states.mark_stale(customer_id)
        return {
            "accepted": True,
            "synthetic": True,
            "environment": "sandbox",
            "message": "Sandbox transaction created. Synchronize transactions to retrieve the latest state.",
        }

    async def fire_webhook(self, customer_id: str) -> dict[str, object]:
        self._require_sandbox()
        await self.plaid.fire_sandbox_webhook(await self._token(customer_id))
        return {"accepted": True, "synthetic": True, "environment": "sandbox", "message": "Sandbox transaction webhook requested."}

    async def create_demo_fraud_scenario(self, customer_id: str) -> dict[str, object]:
        self._require_sandbox()
        await self.simulate_transaction(customer_id, 2500.0, "International Electronics Purchase")
        return {
            "scenario_created": True,
            "synthetic": True,
            "environment": "sandbox",
            "message": "Suspicious transaction scenario generated. Fraud assessment must be performed by Fraud MCP.",
        }
