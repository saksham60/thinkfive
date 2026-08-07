from __future__ import annotations

from typing import Any, Protocol

from fastmcp import Client

from case.app.errors import CaseMcpError


def unwrap(result: Any, provider: str) -> Any:
    value = result.structured_content or {}
    if "result" in value:
        value = value["result"]
    if not isinstance(value, dict) or not value.get("success", False):
        raise CaseMcpError(f"{provider.upper()}_PROVIDER_UNAVAILABLE", f"{provider.title()} MCP could not provide verified evidence.", retryable=True)
    return value.get("data")


class BankingDataProvider(Protocol):
    async def get_accounts(self, customer_id: str) -> Any: ...
    async def get_account_summary(self, customer_id: str) -> Any: ...
    async def get_transaction(self, customer_id: str, transaction_id: str) -> Any: ...
    async def get_customer_identity(self, customer_id: str) -> Any: ...


class FraudDataProvider(Protocol):
    async def get_risk_assessment(self, assessment_id: str) -> Any: ...
    async def get_fraud_alert(self, alert_id: str) -> Any: ...
    async def get_fraud_alerts(self, customer_id: str | None = None, status: str | None = None, severity: str | None = None, limit: int = 100) -> Any: ...


class McpProvider:
    def __init__(self, url: str, token: str | None, kind: str) -> None:
        self.url, self.token, self.kind = url, token, kind

    async def call(self, name: str, args: dict[str, Any]) -> Any:
        try:
            async with Client(self.url, auth=self.token) as client:
                return unwrap(await client.call_tool(name, args), self.kind)
        except CaseMcpError:
            raise
        except Exception:
            raise CaseMcpError(f"{self.kind.upper()}_PROVIDER_UNAVAILABLE", f"{self.kind.title()} MCP is unavailable.", retryable=True) from None


class McpBankingDataProvider(McpProvider):
    def __init__(self, url: str, token: str | None = None) -> None:
        super().__init__(url, token, "banking")

    async def get_accounts(self, c: str) -> Any:
        return await self.call("get_accounts", {"customer_id": c})

    async def get_account_summary(self, c: str) -> Any:
        return await self.call("get_account_summary", {"customer_id": c})

    async def get_transaction(self, c: str, t: str) -> Any:
        return await self.call("get_transaction", {"customer_id": c, "transaction_id": t})

    async def get_customer_identity(self, c: str) -> Any:
        return await self.call("get_customer_identity", {"customer_id": c})


class McpFraudDataProvider(McpProvider):
    def __init__(self, url: str, token: str | None = None) -> None:
        super().__init__(url, token, "fraud")

    async def get_risk_assessment(self, a: str) -> Any:
        return await self.call("get_risk_assessment", {"assessment_id": a})

    async def get_fraud_alert(self, a: str) -> Any:
        return await self.call("get_fraud_alert", {"alert_id": a})

    async def get_fraud_alerts(self, customer_id: str | None = None, status: str | None = None, severity: str | None = None, limit: int = 100) -> Any:
        return await self.call("get_fraud_alerts", {"customer_id": customer_id, "status": status, "severity": severity, "limit": limit})


class NullBankingProvider:
    async def get_accounts(self, c: str) -> Any:
        raise CaseMcpError("BANKING_PROVIDER_UNAVAILABLE", "Banking MCP URL is not configured.")

    get_account_summary = get_accounts
    get_customer_identity = get_accounts

    async def get_transaction(self, c: str, t: str) -> Any:
        raise CaseMcpError("BANKING_PROVIDER_UNAVAILABLE", "Banking MCP URL is not configured.")


class NullFraudProvider:
    async def get_fraud_alert(self, a: str) -> Any:
        raise CaseMcpError("FRAUD_PROVIDER_UNAVAILABLE", "Fraud MCP URL is not configured.")

    get_risk_assessment = get_fraud_alert

    async def get_fraud_alerts(self, customer_id: str | None = None, status: str | None = None, severity: str | None = None, limit: int = 100) -> Any:
        raise CaseMcpError("FRAUD_PROVIDER_UNAVAILABLE", "Fraud MCP URL is not configured.")
