from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, TypeVar, cast

from case.app.errors import CaseMcpError
from fraudMCP.app.container import Container as FraudContainer
from fraudMCP.app.errors import (
    BankingProviderCustomerNotFoundError,
    BankingProviderTransactionNotFoundError,
    BankingProviderUnavailableError,
)
from plaidbanking.app.container import Container as BankingContainer
from plaidbanking.app.models.transaction import TransactionSearchFilters
from plaidbanking.app.plaid.exceptions import CustomerNotFoundError, ResourceNotFoundError

T = TypeVar("T")


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    return value


def _dump_dict(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], _dump(value))


class LocalBankingDataProvider:
    """Direct in-process adapter used by both Fraud and Case MCPs."""

    def __init__(self, banking: BankingContainer) -> None:
        self.banking = banking

    async def get_transaction(self, customer_id: str, transaction_id: str) -> dict[str, Any]:
        try:
            return _dump_dict(await self.banking.transaction_service.get(customer_id, transaction_id))
        except CustomerNotFoundError as exc:
            raise BankingProviderCustomerNotFoundError(str(exc)) from None
        except ResourceNotFoundError as exc:
            raise BankingProviderTransactionNotFoundError(str(exc)) from None
        except Exception as exc:
            raise BankingProviderUnavailableError("Banking data is currently unavailable.") from exc

    async def list_recent_transactions(self, customer_id: str, limit: int = 100, account_id: str | None = None) -> list[dict[str, Any]]:
        try:
            values = await self.banking.transaction_service.recent(customer_id, max(1, min(limit, 100)), account_id)
            return [_dump(value) for value in values]
        except CustomerNotFoundError as exc:
            raise BankingProviderCustomerNotFoundError(str(exc)) from None
        except Exception as exc:
            raise BankingProviderUnavailableError("Banking transaction history is unavailable.") from exc

    async def search_transactions(self, customer_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            values = await self.banking.transaction_service.search(customer_id, TransactionSearchFilters.model_validate(filters))
            return [_dump(value) for value in values]
        except Exception as exc:
            raise BankingProviderUnavailableError("Banking transaction search is unavailable.") from exc

    async def get_account_summary(self, customer_id: str) -> dict[str, Any]:
        try:
            return _dump_dict(await self.banking.banking.get_account_summary(customer_id))
        except CustomerNotFoundError as exc:
            raise BankingProviderCustomerNotFoundError(str(exc)) from None
        except Exception as exc:
            raise BankingProviderUnavailableError("Banking account summary is unavailable.") from exc

    async def get_accounts(self, customer_id: str) -> list[dict[str, Any]]:
        try:
            return [_dump(value) for value in await self.banking.banking.get_accounts(customer_id, balance=True)]
        except CustomerNotFoundError as exc:
            raise BankingProviderCustomerNotFoundError(str(exc)) from None
        except Exception as exc:
            raise BankingProviderUnavailableError("Banking accounts are unavailable.") from exc

    async def get_customer_identity(self, customer_id: str) -> dict[str, Any]:
        try:
            return _dump_dict(await self.banking.banking.get_identity(customer_id))
        except Exception as exc:
            raise CaseMcpError("BANKING_PROVIDER_UNAVAILABLE", "Banking identity is unavailable.", retryable=True) from exc


class LocalCaseBankingDataProvider:
    """Maps local Banking failures to Case MCP's stable provider boundary."""

    def __init__(self, banking: LocalBankingDataProvider) -> None:
        self.banking = banking

    async def get_accounts(self, customer_id: str) -> list[dict[str, Any]]:
        return await self._call(self.banking.get_accounts(customer_id))

    async def get_account_summary(self, customer_id: str) -> dict[str, Any]:
        return await self._call(self.banking.get_account_summary(customer_id))

    async def get_transaction(self, customer_id: str, transaction_id: str) -> dict[str, Any]:
        return await self._call(self.banking.get_transaction(customer_id, transaction_id))

    async def get_customer_identity(self, customer_id: str) -> dict[str, Any]:
        return await self._call(self.banking.get_customer_identity(customer_id))

    @staticmethod
    async def _call(operation: Awaitable[T]) -> T:
        try:
            return await operation
        except CaseMcpError:
            raise
        except Exception as exc:
            raise CaseMcpError("BANKING_PROVIDER_UNAVAILABLE", "Banking MCP could not provide verified evidence.", retryable=True) from exc


class LocalFraudDataProvider:
    """Direct Case-to-Fraud adapter; it never recalculates or fabricates risk."""

    def __init__(self, fraud: FraudContainer) -> None:
        self.fraud = fraud

    async def get_risk_assessment(self, assessment_id: str) -> dict[str, Any]:
        try:
            return _dump_dict(await self.fraud.fraud_service.get_risk_assessment(assessment_id))
        except Exception as exc:
            raise CaseMcpError("FRAUD_PROVIDER_UNAVAILABLE", "Fraud MCP could not provide verified evidence.", retryable=True) from exc

    async def get_fraud_alert(self, alert_id: str) -> dict[str, Any]:
        try:
            return _dump_dict(await self.fraud.alert_service.get_fraud_alert(alert_id))
        except Exception as exc:
            raise CaseMcpError("FRAUD_PROVIDER_UNAVAILABLE", "Fraud MCP could not provide verified evidence.", retryable=True) from exc

    async def get_fraud_alerts(
        self, customer_id: str | None = None, status: str | None = None, severity: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        try:
            values = await self.fraud.alert_service.get_fraud_alerts(customer_id, status, severity, limit)
            return [_dump(value) for value in values]
        except Exception as exc:
            raise CaseMcpError("FRAUD_PROVIDER_UNAVAILABLE", "Fraud MCP could not provide verified evidence.", retryable=True) from exc
