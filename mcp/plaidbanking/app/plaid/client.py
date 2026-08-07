from __future__ import annotations

import asyncio
import importlib
import json
import logging
import random
from datetime import date
from typing import Any, Protocol, cast

from plaidbanking.app.config import Settings
from plaidbanking.app.logging import log_event
from plaidbanking.app.plaid.exceptions import PlaidProviderError
from plaidbanking.app.plaid.mapper import plain


class PlaidGateway(Protocol):
    async def accounts(self, access_token: str, *, balance: bool = False) -> dict[str, Any]: ...
    async def sync_transactions(self, access_token: str, cursor: str | None) -> dict[str, Any]: ...
    async def refresh_transactions(self, access_token: str) -> dict[str, Any]: ...
    async def identity(self, access_token: str) -> dict[str, Any]: ...
    async def identity_match(self, access_token: str, user: dict[str, Any]) -> dict[str, Any]: ...
    async def liabilities(self, access_token: str) -> dict[str, Any]: ...
    async def item(self, access_token: str) -> dict[str, Any]: ...
    async def create_sandbox_item(self, institution_id: str, webhook: str | None) -> tuple[str, str]: ...
    async def create_sandbox_transaction(self, access_token: str, amount: float, description: str, transaction_date: str | None) -> dict[str, Any]: ...
    async def fire_sandbox_webhook(self, access_token: str) -> dict[str, Any]: ...
    async def webhook_key(self, key_id: str) -> dict[str, Any]: ...


_REQUESTS: dict[str, tuple[str, str]] = {
    "accounts_get": ("accounts_get_request", "AccountsGetRequest"),
    "accounts_balance_get": ("accounts_balance_get_request", "AccountsBalanceGetRequest"),
    "transactions_sync": ("transactions_sync_request", "TransactionsSyncRequest"),
    "transactions_refresh": ("transactions_refresh_request", "TransactionsRefreshRequest"),
    "identity_get": ("identity_get_request", "IdentityGetRequest"),
    "identity_match": ("identity_match_request", "IdentityMatchRequest"),
    "liabilities_get": ("liabilities_get_request", "LiabilitiesGetRequest"),
    "item_get": ("item_get_request", "ItemGetRequest"),
    "sandbox_public_token_create": ("sandbox_public_token_create_request", "SandboxPublicTokenCreateRequest"),
    "item_public_token_exchange": ("item_public_token_exchange_request", "ItemPublicTokenExchangeRequest"),
    "sandbox_transactions_create": ("sandbox_transactions_create_request", "SandboxTransactionsCreateRequest"),
    "sandbox_item_fire_webhook": ("sandbox_item_fire_webhook_request", "SandboxItemFireWebhookRequest"),
    "webhook_verification_key_get": ("webhook_verification_key_get_request", "WebhookVerificationKeyGetRequest"),
}


def _model(module: str, name: str, *args: Any, **kwargs: Any) -> Any:
    cls = getattr(importlib.import_module(f"plaid.model.{module}"), name)
    return cls(*args, **kwargs)


class PlaidClient(PlaidGateway):
    RETRYABLE_TYPES = {"API_ERROR", "RATE_LIMIT_EXCEEDED", "INSTITUTION_ERROR"}

    def __init__(self, settings: Settings, api: Any | None = None) -> None:
        self.settings = settings
        self._logger = logging.getLogger(__name__)
        self._api = api or self._build_api()

    def _build_api(self) -> Any:
        import plaid
        from plaid.api import plaid_api

        environments = {
            "sandbox": plaid.Environment.Sandbox,
            "development": getattr(plaid.Environment, "Development", "https://development.plaid.com"),
            "production": plaid.Environment.Production,
        }
        configuration = plaid.Configuration(
            host=environments[self.settings.plaid_env],
            api_key={"clientId": self.settings.plaid_client_id.get_secret_value(), "secret": self.settings.plaid_secret.get_secret_value()},
        )
        configuration.api_key_prefix = {"clientId": "", "secret": ""}
        api_client = plaid.ApiClient(configuration)
        api_client.rest_client.pool_manager.connection_pool_kw["timeout"] = self.settings.plaid_timeout_seconds
        return plaid_api.PlaidApi(api_client)

    async def _call(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        module, name = _REQUESTS[endpoint]
        request = _model(module, name, **kwargs)
        for attempt in range(self.settings.plaid_max_retries + 1):
            try:
                result = await asyncio.to_thread(getattr(self._api, endpoint), request)
                payload = cast(dict[str, Any], plain(result))
                log_event(
                    self._logger,
                    logging.INFO,
                    "plaid_request",
                    provider="plaid",
                    endpoint=endpoint,
                    retry_count=attempt,
                    success=True,
                    plaid_request_id=payload.get("request_id"),
                )
                # Provider credentials remain inside the gateway/service boundary. Callers
                # receive mapped domain models, never this raw payload.
                return payload
            except Exception as exc:
                error = self._translate_error(exc)
                log_event(
                    self._logger,
                    logging.WARNING,
                    "plaid_request_failed",
                    provider="plaid",
                    endpoint=endpoint,
                    retry_count=attempt,
                    success=False,
                    error_category=error.code,
                    plaid_request_id=error.request_id,
                )
                if not error.retryable or attempt >= self.settings.plaid_max_retries:
                    raise error from None
                await asyncio.sleep(min(2**attempt * 0.25 + random.uniform(0, 0.1), 2.0))
        raise AssertionError("unreachable")

    def _translate_error(self, exc: Exception) -> PlaidProviderError:
        payload: dict[str, Any] = {}
        body = getattr(exc, "body", None)
        if body:
            try:
                payload = json.loads(body)
            except (TypeError, json.JSONDecodeError):
                payload = {}
        error_type = str(payload.get("error_type", ""))
        status = int(getattr(exc, "status", 0) or 0)
        retryable = error_type in self.RETRYABLE_TYPES or status == 429 or status >= 500 or isinstance(exc, (TimeoutError, ConnectionError))
        code = str(payload.get("error_code") or ("PLAID_TIMEOUT" if isinstance(exc, TimeoutError) else "PLAID_PROVIDER_ERROR"))
        # Provider messages are not propagated because upstream errors can echo
        # request material. The stable error code carries actionable semantics.
        safe_message = "Plaid could not complete the banking request."
        return PlaidProviderError(safe_message, error_code=code, retryable=retryable, request_id=payload.get("request_id"))

    async def accounts(self, access_token: str, *, balance: bool = False) -> dict[str, Any]:
        return await self._call("accounts_balance_get" if balance else "accounts_get", access_token=access_token)

    async def sync_transactions(self, access_token: str, cursor: str | None) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"access_token": access_token}
        if cursor:
            kwargs["cursor"] = cursor
        return await self._call("transactions_sync", **kwargs)

    async def refresh_transactions(self, access_token: str) -> dict[str, Any]:
        return await self._call("transactions_refresh", access_token=access_token)

    async def identity(self, access_token: str) -> dict[str, Any]:
        return await self._call("identity_get", access_token=access_token)

    async def identity_match(self, access_token: str, user: dict[str, Any]) -> dict[str, Any]:
        if isinstance(user.get("address"), dict):
            user = dict(user)
            user["address"] = _model("address_data_nullable_no_required_fields", "AddressDataNullableNoRequiredFields", **user["address"])
        match_user = _model("identity_match_user", "IdentityMatchUser", **user)
        return await self._call("identity_match", access_token=access_token, user=match_user)

    async def liabilities(self, access_token: str) -> dict[str, Any]:
        return await self._call("liabilities_get", access_token=access_token)

    async def item(self, access_token: str) -> dict[str, Any]:
        return await self._call("item_get", access_token=access_token)

    async def create_sandbox_item(self, institution_id: str, webhook: str | None) -> tuple[str, str]:
        products = [_model("products", "Products", "transactions"), _model("products", "Products", "identity")]
        options_kwargs: dict[str, Any] = {"override_username": "user_transactions_dynamic", "override_password": "pass_good"}
        if webhook:
            options_kwargs["webhook"] = webhook
        options = _model("sandbox_public_token_create_request_options", "SandboxPublicTokenCreateRequestOptions", **options_kwargs)
        kwargs: dict[str, Any] = {"institution_id": institution_id, "initial_products": products, "options": options}
        created = await self._call("sandbox_public_token_create", **kwargs)
        exchanged = await self._call("item_public_token_exchange", public_token=created["public_token"])
        return exchanged["access_token"], exchanged["item_id"]

    async def create_sandbox_transaction(self, access_token: str, amount: float, description: str, transaction_date: str | None) -> dict[str, Any]:
        posted = date.fromisoformat(transaction_date) if transaction_date else date.today()
        transaction = _model(
            "custom_sandbox_transaction",
            "CustomSandboxTransaction",
            date_transacted=posted,
            date_posted=posted,
            amount=amount,
            description=description,
        )
        return await self._call("sandbox_transactions_create", access_token=access_token, transactions=[transaction])

    async def fire_sandbox_webhook(self, access_token: str) -> dict[str, Any]:
        return await self._call("sandbox_item_fire_webhook", access_token=access_token, webhook_code="SYNC_UPDATES_AVAILABLE")

    async def webhook_key(self, key_id: str) -> dict[str, Any]:
        return await self._call("webhook_verification_key_get", key_id=key_id)
