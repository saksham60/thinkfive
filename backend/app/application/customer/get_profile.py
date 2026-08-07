"""Use case: get customer profile."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.customer.entities import Customer
    from app.infrastructure.repositories.customer import PostgresCustomerRepository


class GetProfileUseCase:
    """Retrieves a customer profile."""

    def __init__(self, customer_repo: PostgresCustomerRepository) -> None:
        self.customer_repo = customer_repo

    async def execute(self, customer_id: str) -> Customer | None:
        return await self.customer_repo.get(customer_id)
