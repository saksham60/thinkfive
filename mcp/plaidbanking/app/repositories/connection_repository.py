from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class BankingConnection:
    customer_id: str
    provider: str
    status: str
    external_item_id: str | None = None
    last_synced_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class BankingConnectionRepository(ABC):
    @abstractmethod
    async def get(self, customer_id: str) -> BankingConnection | None: ...


class SupabaseBankingConnectionRepository(BankingConnectionRepository):
    def __init__(self, client: Any) -> None:
        self.client = client

    async def get(self, customer_id: str) -> BankingConnection | None:
        result = await asyncio.to_thread(
            lambda: self.client.table("banking_connections").select("*").eq("customer_id", customer_id).limit(1).execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        last_synced_at = row.get("last_synced_at")
        return BankingConnection(
            customer_id=str(row["customer_id"]),
            provider=str(row.get("provider") or "SYNTHETIC"),
            status=str(row.get("status") or "CONNECTED"),
            external_item_id=row.get("external_item_id"),
            last_synced_at=datetime.fromisoformat(last_synced_at.replace("Z", "+00:00")) if isinstance(last_synced_at, str) else last_synced_at,
            metadata=row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
        )
