from __future__ import annotations

import asyncio

from plaidbanking.app.config import Settings
from plaidbanking.app.plaid.client import PlaidGateway
from plaidbanking.app.plaid.exceptions import BankingError
from plaidbanking.app.repositories.item_repository import ItemRepository


class SandboxBootstrapService:
    def __init__(self, settings: Settings, plaid: PlaidGateway, items: ItemRepository) -> None:
        self.settings = settings
        self.plaid = plaid
        self.items = items
        self._lock = asyncio.Lock()

    async def bootstrap(self) -> bool:
        if not self.settings.plaid_auto_bootstrap:
            return False
        if self.settings.plaid_env != "sandbox":
            raise BankingError("Automatic bootstrap is only allowed in the Plaid Sandbox.")
        async with self._lock:
            customer_id = self.settings.plaid_default_customer_id
            if await self.items.exists(customer_id):
                return False
            access_token, item_id = await self.plaid.create_sandbox_item(self.settings.plaid_institution_id, self.settings.plaid_webhook_url)
            await self.items.register_item(customer_id, access_token, item_id)
            return True
