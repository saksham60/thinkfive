from __future__ import annotations

from dataclasses import replace

from plaidbanking.app.models.common import utc_now
from plaidbanking.app.models.transaction import SyncSummary, Transaction, TransactionSearchFilters
from plaidbanking.app.plaid.client import PlaidGateway
from plaidbanking.app.plaid.exceptions import CustomerNotFoundError, PlaidProviderError, ResourceNotFoundError
from plaidbanking.app.plaid.mapper import map_transaction
from plaidbanking.app.repositories.item_repository import ItemNotFoundError, ItemRepository
from plaidbanking.app.repositories.sync_state_repository import SyncStateRepository
from plaidbanking.app.repositories.transaction_repository import TransactionNotFoundError, TransactionRepository


class TransactionService:
    def __init__(self, plaid: PlaidGateway, items: ItemRepository, transactions: TransactionRepository, sync_states: SyncStateRepository) -> None:
        self.plaid = plaid
        self.items = items
        self.transactions = transactions
        self.sync_states = sync_states

    async def _token(self, customer_id: str) -> str:
        try:
            return await self.items.get_access_token(customer_id)
        except ItemNotFoundError:
            raise CustomerNotFoundError("No banking connection exists for this customer.") from None

    async def sync(self, customer_id: str) -> SyncSummary:
        async with self.sync_states.lock_for(customer_id):
            token = await self._token(customer_id)
            original = await self.sync_states.get(customer_id)
            await self.sync_states.save(replace(original, status="synchronizing"))
            cursor = original.cursor
            added: list[Transaction] = []
            modified: list[Transaction] = []
            removed: list[str] = []
            pages = 0
            mutation_restarts = 0
            try:
                while True:
                    try:
                        page = await self.plaid.sync_transactions(token, cursor)
                    except PlaidProviderError as exc:
                        if exc.code != "TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION" or mutation_restarts >= 2:
                            raise
                        # Plaid requires the whole page loop to restart from the
                        # previously committed cursor when data mutates mid-sync.
                        mutation_restarts += 1
                        cursor = original.cursor
                        added.clear()
                        modified.clear()
                        removed.clear()
                        pages = 0
                        continue
                    pages += 1
                    added.extend(map_transaction(customer_id, value) for value in page.get("added", []))
                    modified.extend(map_transaction(customer_id, value) for value in page.get("modified", []))
                    removed.extend(value["transaction_id"] if isinstance(value, dict) else str(value) for value in page.get("removed", []))
                    next_cursor = page.get("next_cursor")
                    if next_cursor is None:
                        raise RuntimeError("Plaid sync response did not include next_cursor")
                    cursor = next_cursor
                    if not page.get("has_more", False):
                        break
                # Repository mutation precedes cursor commit. apply_changes is atomic for Phase 1.
                await self.transactions.apply_changes(customer_id, added + modified, removed)
                await self.sync_states.save(replace(original, cursor=cursor, last_sync_at=utc_now(), status="synchronized", stale=False))
            except Exception:
                await self.sync_states.save(replace(original, status="failed", stale=True))
                raise
            return SyncSummary(
                added_count=len(added),
                modified_count=len(modified),
                removed_count=len(removed),
                current_repository_count=await self.transactions.count(customer_id),
                pages_processed=pages,
            )

    async def ensure_synchronized(self, customer_id: str) -> None:
        state = await self.sync_states.get(customer_id)
        if state.stale or state.last_sync_at is None:
            await self.sync(customer_id)

    async def recent(self, customer_id: str, limit: int = 20, account_id: str | None = None) -> list[Transaction]:
        await self.ensure_synchronized(customer_id)
        return await self.transactions.list_recent_transactions(customer_id, limit, account_id)

    async def get(self, customer_id: str, transaction_id: str) -> Transaction:
        await self.ensure_synchronized(customer_id)
        try:
            return await self.transactions.get_transaction(customer_id, transaction_id)
        except TransactionNotFoundError:
            raise ResourceNotFoundError("Transaction was not found for this customer.") from None

    async def search(self, customer_id: str, filters: TransactionSearchFilters) -> list[Transaction]:
        await self.ensure_synchronized(customer_id)
        return await self.transactions.search_transactions(customer_id, filters)

    async def refresh(self, customer_id: str) -> dict[str, object]:
        await self.plaid.refresh_transactions(await self._token(customer_id))
        await self.sync_states.mark_stale(customer_id)
        return {
            "accepted": True,
            "message": "Plaid refresh accepted. Updated data may arrive asynchronously via webhook and a subsequent synchronization.",
        }
