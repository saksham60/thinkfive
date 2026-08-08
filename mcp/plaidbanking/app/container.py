from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from plaidbanking.app.config import Settings
from plaidbanking.app.plaid.client import PlaidClient, PlaidGateway
from plaidbanking.app.repositories import (
    InMemoryItemRepository,
    InMemorySyncStateRepository,
    InMemoryTransactionRepository,
    InMemoryWebhookEventRepository,
    ItemRepository,
    SupabaseAccountRepository,
    SupabaseBankingConnectionRepository,
    SupabaseTransactionRepository,
    SyncStateRepository,
    TransactionRepository,
    WebhookEventRepository,
)
from plaidbanking.app.services import (
    BankingService,
    SandboxBootstrapService,
    SandboxService,
    SupabaseBankingService,
    SupabaseSimulationService,
    SupabaseTransactionService,
    TransactionService,
)


@dataclass(slots=True)
class Container:
    settings: Settings
    source: str
    plaid: PlaidGateway | None
    items: ItemRepository
    transactions: TransactionRepository
    sync_states: SyncStateRepository
    webhook_events: WebhookEventRepository
    banking: BankingService | SupabaseBankingService
    transaction_service: TransactionService | SupabaseTransactionService
    sandbox: SandboxService | SupabaseSimulationService
    bootstrap: SandboxBootstrapService | None


def create_container(settings: Settings, plaid: PlaidGateway | None = None, *, supabase_client: Any = None) -> Container:
    items = InMemoryItemRepository()
    states = InMemorySyncStateRepository()
    events = InMemoryWebhookEventRepository()
    if settings.banking_data_provider == "supabase":
        if supabase_client is None:
            raise ValueError("A shared Supabase client is required when BANKING_DATA_PROVIDER=supabase")
        accounts = SupabaseAccountRepository(supabase_client)
        connections = SupabaseBankingConnectionRepository(supabase_client)
        supabase_transactions = SupabaseTransactionRepository(supabase_client)
        return Container(
            settings=settings,
            source="supabase",
            plaid=None,
            items=items,
            transactions=supabase_transactions,
            sync_states=states,
            webhook_events=events,
            banking=SupabaseBankingService(accounts, connections),
            transaction_service=SupabaseTransactionService(supabase_transactions, connections),
            sandbox=SupabaseSimulationService(accounts, supabase_transactions, connections),
            bootstrap=None,
        )

    gateway = plaid or PlaidClient(settings)
    memory_transactions = InMemoryTransactionRepository()
    return Container(
        settings=settings,
        source=f"plaid_{settings.plaid_env}",
        plaid=gateway,
        items=items,
        transactions=memory_transactions,
        sync_states=states,
        webhook_events=events,
        banking=BankingService(gateway, items, states),
        transaction_service=TransactionService(gateway, items, memory_transactions, states),
        sandbox=SandboxService(settings, gateway, items, states),
        bootstrap=SandboxBootstrapService(settings, gateway, items),
    )
