from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from plaidbanking.app.models.account import Account, AccountBalance, AccountSummary
from plaidbanking.app.models.identity import CustomerIdentity, IdentityVerification
from plaidbanking.app.models.liability import Liabilities
from plaidbanking.app.models.transaction import SyncSummary, Transaction, TransactionSearchFilters
from plaidbanking.app.plaid.exceptions import CustomerNotFoundError, InvalidInputError, ResourceNotFoundError
from plaidbanking.app.repositories.account_repository import AccountRepository
from plaidbanking.app.repositories.connection_repository import BankingConnection, BankingConnectionRepository
from plaidbanking.app.repositories.transaction_repository import SupabaseTransactionRepository, TransactionNotFoundError


class SupabaseBankingService:
    def __init__(self, accounts: AccountRepository, connections: BankingConnectionRepository) -> None:
        self.accounts = accounts
        self.connections = connections

    async def _connection(self, customer_id: str) -> BankingConnection:
        connection = await self.connections.get(customer_id)
        if connection is None:
            raise CustomerNotFoundError("No banking connection exists for this customer.")
        return connection

    async def get_accounts(self, customer_id: str, *, balance: bool = False) -> list[Account]:
        await self._connection(customer_id)
        return await self.accounts.list_accounts(customer_id)

    async def get_account_summary(self, customer_id: str) -> AccountSummary:
        return AccountSummary.from_accounts(await self.get_accounts(customer_id, balance=True))

    async def get_account_balance(self, customer_id: str, account_id: str) -> AccountBalance:
        await self._connection(customer_id)
        account = await self.accounts.get_account(customer_id, account_id)
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
        await self._connection(customer_id)
        return CustomerIdentity(capability_available=False)

    async def verify_identity(
        self, customer_id: str, *, name: str | None, phone: str | None, email: str | None, address: dict[str, Any] | None
    ) -> IdentityVerification:
        await self._connection(customer_id)
        if not any(value is not None for value in (name, phone, email, address)):
            raise ValueError("At least one identity attribute is required.")
        return IdentityVerification(capability_available=False, reason="Identity verification is not available from the canonical Supabase banking store.")

    async def get_liabilities(self, customer_id: str) -> Liabilities:
        await self._connection(customer_id)
        return Liabilities(capability_available=False, reason="Liabilities are not available from the canonical Supabase banking store.")

    async def connection_status(self, customer_id: str) -> dict[str, Any]:
        connection = await self._connection(customer_id)
        healthy = connection.status.upper() == "CONNECTED"
        return {
            "healthy": healthy,
            "provider": connection.provider,
            "transaction_state": "current" if healthy else "unavailable",
            "synchronization_status": "synchronized" if healthy else connection.status.casefold(),
            "last_transaction_sync": connection.last_synced_at,
        }


class SupabaseTransactionService:
    def __init__(self, transactions: SupabaseTransactionRepository, connections: BankingConnectionRepository) -> None:
        self.transactions = transactions
        self.connections = connections

    async def _require_customer(self, customer_id: str) -> None:
        if await self.connections.get(customer_id) is None:
            raise CustomerNotFoundError("No banking connection exists for this customer.")

    async def sync(self, customer_id: str) -> SyncSummary:
        await self._require_customer(customer_id)
        return SyncSummary(current_repository_count=await self.transactions.count(customer_id))

    async def ensure_synchronized(self, customer_id: str) -> None:
        await self._require_customer(customer_id)

    async def recent(self, customer_id: str, limit: int = 20, account_id: str | None = None) -> list[Transaction]:
        await self._require_customer(customer_id)
        return await self.transactions.list_recent_transactions(customer_id, limit, account_id)

    async def get(self, customer_id: str, transaction_id: str) -> Transaction:
        await self._require_customer(customer_id)
        try:
            return await self.transactions.get_transaction(customer_id, transaction_id)
        except TransactionNotFoundError:
            raise ResourceNotFoundError("Transaction was not found for this customer.") from None

    async def search(self, customer_id: str, filters: TransactionSearchFilters) -> list[Transaction]:
        await self._require_customer(customer_id)
        return await self.transactions.search_transactions(customer_id, filters)

    async def refresh(self, customer_id: str) -> dict[str, object]:
        await self._require_customer(customer_id)
        return {
            "accepted": True,
            "refreshed": False,
            "provider": "supabase",
            "message": "The canonical Supabase banking store is already current; no external refresh is required.",
        }


class SupabaseSimulationService:
    def __init__(self, accounts: AccountRepository, transactions: SupabaseTransactionRepository, connections: BankingConnectionRepository) -> None:
        self.accounts = accounts
        self.transactions = transactions
        self.connections = connections

    async def _account(self, customer_id: str) -> Account:
        if await self.connections.get(customer_id) is None:
            raise CustomerNotFoundError("No banking connection exists for this customer.")
        accounts = await self.accounts.list_accounts(customer_id)
        credit = sorted((account for account in accounts if account.type.casefold() == "credit"), key=lambda account: account.account_id)
        if credit:
            return credit[0]
        depository = sorted(
            (account for account in accounts if account.type.casefold() == "depository"), key=lambda account: account.account_id
        )
        if depository:
            return depository[0]
        raise ResourceNotFoundError("No active credit or depository account exists for this customer.")

    async def simulate_transaction(self, customer_id: str, amount: float, description: str, transaction_date: date | None = None) -> dict[str, Any]:
        if Decimal(str(amount)) == 0 or not description.strip():
            raise InvalidInputError("A non-zero amount and description are required.")
        account = await self._account(customer_id)
        exact_description = description
        merchant_name = description.strip()
        is_demo_fraud = merchant_name.casefold() == "international electronics purchase"
        now = datetime.now(UTC)
        transaction = Transaction(
            customer_id=customer_id,
            transaction_id=f"txn_{uuid4()}",
            account_id=account.account_id,
            amount=Decimal(str(amount)),
            currency=account.currency or "USD",
            merchant_name=merchant_name,
            transaction_name=exact_description,
            date=transaction_date or now.date(),
            authorized_date=(transaction_date or now.date()),
            datetime=now,
            pending=False,
            category=("Electronics",) if is_demo_fraud else ("Synthetic",),
            personal_finance_category={"primary": "GENERAL_MERCHANDISE", "detailed": "ELECTRONICS"} if is_demo_fraud else None,
            payment_channel="online" if is_demo_fraud else "other",
            location={"city": "Singapore", "country": "SG"} if is_demo_fraud else None,
        )
        persisted = await self.transactions.insert_transaction(transaction)
        payload = persisted.model_dump(mode="json")
        payload.update({"customer_id": customer_id, "description": persisted.transaction_name, "source": "SYNTHETIC"})
        return {
            "accepted": True,
            "synthetic": True,
            "environment": "supabase",
            "provider": "supabase",
            "transaction": payload,
            "message": "Synthetic transaction persisted in the canonical Supabase banking store.",
        }

    async def fire_webhook(self, customer_id: str) -> dict[str, object]:
        if await self.connections.get(customer_id) is None:
            raise CustomerNotFoundError("No banking connection exists for this customer.")
        return {
            "accepted": False,
            "synthetic": True,
            "environment": "supabase",
            "provider": "supabase",
            "message": "Plaid transaction webhooks are not used while Supabase is the canonical banking source.",
        }

    async def create_demo_fraud_scenario(self, customer_id: str) -> dict[str, object]:
        created = await self.simulate_transaction(customer_id, 2500.0, "International Electronics Purchase")
        return {
            **created,
            "scenario_created": True,
            "message": "Suspicious synthetic transaction persisted. Fraud assessment remains the responsibility of Fraud MCP.",
        }
