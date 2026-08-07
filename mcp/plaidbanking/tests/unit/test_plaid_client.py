from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from plaidbanking.app.config import Settings
from plaidbanking.app.plaid.client import PlaidClient
from plaidbanking.app.plaid.exceptions import PlaidProviderError


class ProviderException(Exception):
    def __init__(self, status: int, payload: dict[str, object]) -> None:
        super().__init__("unsafe provider exception")
        self.status = status
        self.body = json.dumps(payload)


class FakeApi:
    def __init__(self, failures: list[Exception]) -> None:
        self.failures = failures
        self.calls = 0

    def transactions_refresh(self, request: object) -> dict[str, str]:
        self.calls += 1
        if self.failures:
            raise self.failures.pop(0)
        return {"request_id": "request-safe"}


def configured(retries: int = 2) -> Settings:
    return Settings(
        _env_file=None,
        PLAID_CLIENT_ID="client",
        PLAID_SECRET="provider-secret-value",
        PLAID_AUTO_BOOTSTRAP=False,
        PLAID_MAX_RETRIES=retries,
    )


@pytest.mark.asyncio
async def test_retryable_5xx_uses_bounded_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    api = FakeApi([ProviderException(500, {"error_type": "API_ERROR", "error_code": "INTERNAL_SERVER_ERROR"})])
    monkeypatch.setattr("plaidbanking.app.plaid.client.asyncio.sleep", AsyncMock())
    result = await PlaidClient(configured(), api=api).refresh_transactions("internal-token")
    assert result["request_id"] == "request-safe" and api.calls == 2


@pytest.mark.asyncio
async def test_rate_limit_retries_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    failures = [ProviderException(429, {"error_type": "RATE_LIMIT_EXCEEDED", "error_code": "RATE_LIMIT_EXCEEDED"}) for _ in range(3)]
    api = FakeApi(failures)
    monkeypatch.setattr("plaidbanking.app.plaid.client.asyncio.sleep", AsyncMock())
    with pytest.raises(PlaidProviderError) as raised:
        await PlaidClient(configured(retries=2), api=api).refresh_transactions("internal-token")
    assert raised.value.retryable is True and api.calls == 3


@pytest.mark.asyncio
async def test_nonretryable_4xx_is_not_retried_and_secret_is_redacted(monkeypatch: pytest.MonkeyPatch) -> None:
    api = FakeApi(
        [
            ProviderException(
                400,
                {
                    "error_type": "INVALID_INPUT",
                    "error_code": "INVALID_ACCESS_TOKEN",
                    "display_message": "provider-secret-value internal-token",
                },
            )
        ]
    )
    sleep = AsyncMock()
    monkeypatch.setattr("plaidbanking.app.plaid.client.asyncio.sleep", sleep)
    with pytest.raises(PlaidProviderError) as raised:
        await PlaidClient(configured(), api=api).refresh_transactions("internal-token")
    assert api.calls == 1 and not sleep.called
    assert "provider-secret-value" not in str(raised.value)
    assert "internal-token" not in str(raised.value)
