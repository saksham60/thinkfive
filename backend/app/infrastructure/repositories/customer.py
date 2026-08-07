"""Customer repository implementation."""

from __future__ import annotations

from app.domain.customer.entities import Customer, CustomerCard
from app.infrastructure.database.postgres import PostgresDatabase


class PostgresCustomerRepository:
    """PostgreSQL implementation of CustomerRepository port."""

    def __init__(self, db: PostgresDatabase) -> None:
        self.db = db

    async def get(self, customer_id: str) -> Customer | None:
        row = await self.db.fetchrow(
            "SELECT * FROM customer_profiles WHERE customer_id = $1",
            customer_id,
        )
        if row is None:
            return None
        return _row_to_customer(row)

    async def create(self, customer: Customer) -> Customer:
        row = await self.db.fetchrow(
            """
            INSERT INTO customer_profiles
                (customer_id, email, phone, first_name, last_name, preferred_language, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (customer_id) DO UPDATE SET updated_at = NOW()
            RETURNING *
            """,
            customer.customer_id,
            customer.email,
            customer.phone,
            customer.first_name,
            customer.last_name,
            customer.preferred_language,
            customer.metadata,
        )
        assert row is not None
        return _row_to_customer(row)

    async def update(self, customer: Customer) -> Customer:
        row = await self.db.fetchrow(
            """
            UPDATE customer_profiles
            SET email = $2, phone = $3, first_name = $4, last_name = $5,
                preferred_language = $6, metadata = $7, updated_at = NOW()
            WHERE customer_id = $1
            RETURNING *
            """,
            customer.customer_id,
            customer.email,
            customer.phone,
            customer.first_name,
            customer.last_name,
            customer.preferred_language,
            customer.metadata,
        )
        assert row is not None
        return _row_to_customer(row)

    async def get_card(self, card_id: str) -> CustomerCard | None:
        row = await self.db.fetchrow(
            "SELECT * FROM customer_cards WHERE card_id = $1",
            card_id,
        )
        if row is None:
            return None
        return _row_to_card(row)

    async def get_customer_cards(self, customer_id: str) -> list[CustomerCard]:
        rows = await self.db.fetch(
            "SELECT * FROM customer_cards WHERE customer_id = $1 ORDER BY is_primary DESC",
            customer_id,
        )
        return [_row_to_card(r) for r in rows]


def _row_to_customer(row: object) -> Customer:
    return Customer(
        customer_id=row["customer_id"],  # type: ignore[index]
        email=row["email"],  # type: ignore[index]
        phone=row["phone"],  # type: ignore[index]
        first_name=row["first_name"],  # type: ignore[index]
        last_name=row["last_name"],  # type: ignore[index]
        preferred_language=row["preferred_language"],  # type: ignore[index]
        created_at=row["created_at"],  # type: ignore[index]
        updated_at=row["updated_at"],  # type: ignore[index]
        metadata=row["metadata"],  # type: ignore[index]
    )


def _row_to_card(row: object) -> CustomerCard:
    return CustomerCard(
        card_id=row["card_id"],  # type: ignore[index]
        customer_id=row["customer_id"],  # type: ignore[index]
        card_last_four=row["card_last_four"],  # type: ignore[index]
        card_brand=row["card_brand"],  # type: ignore[index]
        card_type=row["card_type"],  # type: ignore[index]
        is_primary=row["is_primary"],  # type: ignore[index]
        created_at=row["created_at"],  # type: ignore[index]
        metadata=row["metadata"],  # type: ignore[index]
    )
