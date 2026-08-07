from __future__ import annotations

from dataclasses import dataclass

from plaidbanking.app.config import Settings
from plaidbanking.app.plaid.client import PlaidClient, PlaidGateway
from plaidbanking.app.repositories import (
    InMemoryItemRepository,
    InMemorySyncStateRepository,
    InMemoryTransactionRepository,
    InMemoryWebhookEventRepository,
    ItemRepository,
    SyncStateRepository,
    TransactionRepository,
    WebhookEventRepository,
)
from plaidbanking.app.services import BankingService, SandboxBootstrapService, SandboxService, TransactionService


@dataclass(slots=True)
class Container:
    settings: Settings
    plaid: PlaidGateway
    items: ItemRepository
    transactions: TransactionRepository
    sync_states: SyncStateRepository
    webhook_events: WebhookEventRepository
    banking: BankingService
    transaction_service: TransactionService
    sandbox: SandboxService
    bootstrap: SandboxBootstrapService


def create_container(settings: Settings, plaid: PlaidGateway | None = None) -> Container:
    gateway = plaid or PlaidClient(settings)
    items = InMemoryItemRepository()
    transactions = InMemoryTransactionRepository()
    states = InMemorySyncStateRepository()
    events = InMemoryWebhookEventRepository()
    return Container(
        settings=settings,
        plaid=gateway,
        items=items,
        transactions=transactions,
        sync_states=states,
        webhook_events=events,
        banking=BankingService(gateway, items, states),
        transaction_service=TransactionService(gateway, items, transactions, states),
        sandbox=SandboxService(settings, gateway, items, states),
        bootstrap=SandboxBootstrapService(settings, gateway, items),
    )
