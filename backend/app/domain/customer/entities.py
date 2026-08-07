"""Domain layer - Customer entities and ports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class CustomerId:
    """Customer identifier value object."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Customer ID cannot be empty")


@dataclass
class Customer:
    """Customer entity."""

    customer_id: str
    email: str | None = None
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    preferred_language: str = "en"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, object] | None = None

    @property
    def display_name(self) -> str:
        """Get customer display name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.email:
            return self.email
        return self.customer_id


@dataclass
class CustomerCard:
    """Customer card metadata."""

    card_id: str
    customer_id: str
    card_last_four: str | None = None
    card_brand: str | None = None
    card_type: str | None = None
    is_primary: bool = False
    created_at: datetime | None = None
    metadata: dict[str, object] | None = None


class CustomerRepository(Protocol):
    """Repository port for customer persistence."""

    async def get(self, customer_id: str) -> Customer | None:
        """Retrieve customer by ID."""
        ...

    async def create(self, customer: Customer) -> Customer:
        """Create new customer."""
        ...

    async def update(self, customer: Customer) -> Customer:
        """Update existing customer."""
        ...

    async def get_card(self, card_id: str) -> CustomerCard | None:
        """Retrieve card metadata."""
        ...

    async def get_customer_cards(self, customer_id: str) -> list[CustomerCard]:
        """Get all cards for customer."""
        ...
