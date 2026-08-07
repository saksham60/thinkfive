from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from collections.abc import Mapping
from typing import Any, Protocol

import httpx
from fastmcp import Client

from fraudMCP.app.errors import (
    BankingProviderCustomerNotFoundError,
    BankingProviderMalformedResponseError,
    BankingProviderTimeoutError,
    BankingProviderTransactionNotFoundError,
    BankingProviderUnauthorizedError,
    BankingProviderUnavailableError,
)
from fraudMCP.app.logging import log_event


class BankingDataProvider(Protocol):
    async def get_transaction(self, customer_id: str, transaction_id: str) -> dict[str, Any]: ...

    async def list_recent_transactions(self, customer_id: str, limit: int = 100, account_id: str | None = None) -> list[dict[str, Any]]: ...

    async def search_transactions(self, customer_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]: ...

    async def get_account_summary(self, customer_id: str) -> dict[str, Any]: ...

    async def get_accounts(self, customer_id: str) -> list[dict[str, Any]]: ...


class McpBankingDataProvider(BankingDataProvider):
    """Fetches banking evidence from the Plaid Banking MCP through MCP tool calls."""

    RETRYABLE_HTTP_STATUSES = frozenset({429, 500, 502, 503, 504})

    def __init__(
        self,
        base_url: str,
        *,
        auth_token: str | None,
        timeout_seconds: float,
        max_retries: int,
        max_backoff_seconds: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_backoff_seconds = max_backoff_seconds
        self._logger = logging.getLogger(__name__)

    async def get_transaction(self, customer_id: str, transaction_id: str) -> dict[str, Any]:
        data = await self._call_tool("get_transaction", {"customer_id": customer_id, "transaction_id": transaction_id}, customer_id)
        if not isinstance(data, dict):
            raise BankingProviderMalformedResponseError("Banking provider returned an invalid transaction payload.")
        return data

    async def list_recent_transactions(self, customer_id: str, limit: int = 100, account_id: str | None = None) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        args: dict[str, Any] = {"customer_id": customer_id, "limit": bounded_limit}
        if account_id:
            args["account_id"] = account_id
        data = await self._call_tool("get_recent_transactions", args, customer_id)
        if not isinstance(data, list):
            raise BankingProviderMalformedResponseError("Banking provider returned an invalid recent-transactions payload.")
        return [item for item in data if isinstance(item, dict)]

    async def search_transactions(self, customer_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        args = {"customer_id": customer_id, **filters}
        if "limit" in args:
            args["limit"] = max(1, min(int(args["limit"]), 100))
        data = await self._call_tool("search_transactions", args, customer_id)
        if not isinstance(data, list):
            raise BankingProviderMalformedResponseError("Banking provider returned an invalid search payload.")
        return [item for item in data if isinstance(item, dict)]

    async def get_account_summary(self, customer_id: str) -> dict[str, Any]:
        data = await self._call_tool("get_account_summary", {"customer_id": customer_id}, customer_id)
        if not isinstance(data, dict):
            raise BankingProviderMalformedResponseError("Banking provider returned an invalid account summary payload.")
        return data

    async def get_accounts(self, customer_id: str) -> list[dict[str, Any]]:
        data = await self._call_tool("get_accounts", {"customer_id": customer_id}, customer_id)
        if not isinstance(data, list):
            raise BankingProviderMalformedResponseError("Banking provider returned an invalid accounts payload.")
        return [item for item in data if isinstance(item, dict)]

    async def _call_tool(self, tool_name: str, arguments: dict[str, Any], customer_id: str) -> Any:
        for attempt in range(self.max_retries + 1):
            started_at = time.perf_counter()
            try:
                async with Client(self.base_url, auth=self.auth_token, timeout=self.timeout_seconds) as client:
                    result = await client.call_tool(tool_name, arguments, timeout=self.timeout_seconds, raise_on_error=False)
                payload = self._extract_payload(result)
                envelope = self._extract_envelope(payload)
                if envelope.get("success") is True:
                    response_customer = envelope.get("customer_id")
                    if response_customer and response_customer != customer_id:
                        raise BankingProviderMalformedResponseError("Banking provider customer mismatch detected.")
                    duration_ms = int((time.perf_counter() - started_at) * 1000)
                    log_event(
                        self._logger,
                        logging.INFO,
                        "banking_provider_call",
                        provider="banking_mcp",
                        tool=tool_name,
                        customer_id=customer_id,
                        success=True,
                        retry_count=attempt,
                        provider_latency_ms=duration_ms,
                    )
                    return envelope.get("data")

                code, message, retryable = self._extract_error_fields(envelope)
                mapped = self._map_error(code, message)
                if retryable and attempt < self.max_retries:
                    await asyncio.sleep(self._backoff_seconds(attempt))
                    continue
                raise mapped
            except (httpx.ConnectTimeout, httpx.ReadTimeout, TimeoutError) as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(self._backoff_seconds(attempt))
                    continue
                raise BankingProviderTimeoutError("Banking MCP timed out while processing the request.") from exc
            except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.NetworkError) as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(self._backoff_seconds(attempt))
                    continue
                raise BankingProviderUnavailableError("Banking MCP is currently unavailable.") from exc
            except BankingProviderUnavailableError:
                raise
            except Exception as exc:
                if self._is_retryable_unknown_exception(exc) and attempt < self.max_retries:
                    await asyncio.sleep(self._backoff_seconds(attempt))
                    continue
                raise BankingProviderUnavailableError("Banking MCP request failed unexpectedly.") from exc
        raise BankingProviderUnavailableError("Banking MCP request failed after retries.")

    def _extract_payload(self, result: Any) -> Any:
        if isinstance(result, Mapping):
            return dict(result)

        if hasattr(result, "data") and result.data is not None:
            return result.data

        if isinstance(result, list):
            return result

        if hasattr(result, "content"):
            content = result.content
            if isinstance(content, list):
                for block in content:
                    text = block.text if hasattr(block, "text") else None
                    if isinstance(text, str):
                        parsed = self._try_parse_json(text)
                        if parsed is not None:
                            return parsed
                    if hasattr(block, "model_dump"):
                        dumped = block.model_dump(mode="json")
                        if isinstance(dumped, dict) and "text" in dumped and isinstance(dumped["text"], str):
                            parsed = self._try_parse_json(dumped["text"])
                            if parsed is not None:
                                return parsed

        if hasattr(result, "model_dump"):
            dumped = result.model_dump(mode="json")
            if isinstance(dumped, dict):
                return dumped

        raise BankingProviderMalformedResponseError("Banking MCP returned an unsupported tool response format.")

    def _extract_envelope(self, payload: Any) -> dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, list) and len(payload) == 1 and isinstance(payload[0], dict):
            return payload[0]
        if isinstance(payload, list) and len(payload) == 1 and isinstance(payload[0], str):
            parsed = self._try_parse_json(payload[0])
            if isinstance(parsed, dict):
                return parsed
        raise BankingProviderMalformedResponseError("Banking MCP response envelope is invalid.")

    def _extract_error_fields(self, envelope: dict[str, Any]) -> tuple[str, str, bool]:
        code = str(envelope.get("error_code") or "BANKING_PROVIDER_ERROR")
        message = str(envelope.get("message") or "Banking provider request failed.")
        retryable = bool(envelope.get("retryable", False))
        return code, message, retryable

    def _map_error(self, code: str, message: str) -> Exception:
        normalized = code.upper()
        if normalized in {"UNAUTHORIZED", "BANKING_PROVIDER_UNAUTHORIZED"}:
            return BankingProviderUnauthorizedError(message)
        if normalized == "CUSTOMER_NOT_FOUND":
            return BankingProviderCustomerNotFoundError(message)
        if normalized in {"RESOURCE_NOT_FOUND", "TRANSACTION_NOT_FOUND"}:
            return BankingProviderTransactionNotFoundError(message)
        if normalized in {"PLAID_TIMEOUT", "BANKING_PROVIDER_TIMEOUT"}:
            return BankingProviderTimeoutError(message)
        return BankingProviderUnavailableError(message)

    def _backoff_seconds(self, attempt: int) -> float:
        return float(min((2**attempt) * 0.2 + random.uniform(0.0, 0.08), self.max_backoff_seconds))

    @staticmethod
    def _try_parse_json(value: str) -> Any | None:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def _is_retryable_unknown_exception(self, exc: Exception) -> bool:
        status = getattr(exc, "status_code", None)
        if isinstance(status, int) and status in self.RETRYABLE_HTTP_STATUSES:
            return True
        message = str(exc).upper()
        return "TIMEOUT" in message or "CONNECTION" in message or "UNAVAILABLE" in message
