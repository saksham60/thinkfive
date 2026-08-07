from __future__ import annotations

from typing import Any

from plaidbanking.app.models.account import Account, AccountBalance, AccountSummary
from plaidbanking.app.models.identity import CustomerIdentity, IdentityVerification
from plaidbanking.app.models.liability import Liabilities
from plaidbanking.app.plaid.client import PlaidGateway
from plaidbanking.app.plaid.exceptions import CustomerNotFoundError, ResourceNotFoundError
from plaidbanking.app.plaid.mapper import map_account, map_identity, map_identity_match, map_liabilities
from plaidbanking.app.repositories.item_repository import ItemNotFoundError, ItemRepository
from plaidbanking.app.repositories.sync_state_repository import SyncStateRepository

CAPABILITY_CODES = {"PRODUCTS_NOT_SUPPORTED", "PRODUCT_NOT_READY", "ADDITIONAL_CONSENT_REQUIRED", "NO_ACCOUNTS"}


class BankingService:
    def __init__(self, plaid: PlaidGateway, items: ItemRepository, sync_states: SyncStateRepository) -> None:
        self.plaid = plaid
        self.items = items
        self.sync_states = sync_states

    async def _token(self, customer_id: str) -> str:
        try:
            return await self.items.get_access_token(customer_id)
        except ItemNotFoundError:
            raise CustomerNotFoundError("No banking connection exists for this customer.") from None

    async def get_accounts(self, customer_id: str, *, balance: bool = False) -> list[Account]:
        payload = await self.plaid.accounts(await self._token(customer_id), balance=balance)
        return [map_account(value) for value in payload.get("accounts", [])]

    async def get_account_summary(self, customer_id: str) -> AccountSummary:
        return AccountSummary.from_accounts(await self.get_accounts(customer_id, balance=True))

    async def get_account_balance(self, customer_id: str, account_id: str) -> AccountBalance:
        accounts = await self.get_accounts(customer_id, balance=True)
        account = next((value for value in accounts if value.account_id == account_id), None)
        if account is None:
            raise ResourceNotFoundError("Account was not found for this customer.")
        return AccountBalance(
            account_id=account.account_id,
            account_name=account.name,
            current_balance=account.current_balance,
            available_balance=account.available_balance,
            currency=account.currency,
        )

    async def get_identity(self, customer_id: str) -> CustomerIdentity:
        try:
            return map_identity(await self.plaid.identity(await self._token(customer_id)))
        except Exception as exc:
            if getattr(exc, "code", "") in CAPABILITY_CODES:
                return CustomerIdentity(capability_available=False)
            raise

    async def verify_identity(
        self, customer_id: str, *, name: str | None, phone: str | None, email: str | None, address: dict[str, Any] | None
    ) -> IdentityVerification:
        user = {
            key: value for key, value in {"legal_name": name, "phone_number": phone, "email_address": email, "address": address}.items() if value is not None
        }
        if not user:
            raise ValueError("At least one identity attribute is required.")
        try:
            return map_identity_match(await self.plaid.identity_match(await self._token(customer_id), user))
        except Exception as exc:
            if getattr(exc, "code", "") in CAPABILITY_CODES:
                return IdentityVerification(capability_available=False, reason="Plaid Identity Match is not enabled for this Item.")
            raise

    async def get_liabilities(self, customer_id: str) -> Liabilities:
        try:
            return map_liabilities(await self.plaid.liabilities(await self._token(customer_id)))
        except Exception as exc:
            if getattr(exc, "code", "") in CAPABILITY_CODES:
                return Liabilities(capability_available=False, reason="Plaid Liabilities is not enabled for this Item.")
            raise

    async def connection_status(self, customer_id: str) -> dict[str, Any]:
        payload = await self.plaid.item(await self._token(customer_id))
        item = payload.get("item") or {}
        state = await self.sync_states.get(customer_id)
        error = item.get("error") or None
        return {
            "healthy": error is None,
            "item_id": item.get("item_id"),
            "institution_id": item.get("institution_id"),
            "available_products": item.get("available_products") or [],
            "billed_products": item.get("billed_products") or [],
            "consented_products": item.get("consented_products") or [],
            "item_error": {"error_type": error.get("error_type"), "error_code": error.get("error_code")} if isinstance(error, dict) else None,
            "last_transaction_sync": state.last_sync_at,
            "transaction_state": "stale" if state.stale else "current",
            "synchronization_status": state.status,
            "last_successful_update": ((item.get("status") or {}).get("transactions") or {}).get("last_successful_update"),
        }
