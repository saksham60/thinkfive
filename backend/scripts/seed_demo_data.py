"""Seed demo data for the ThinkFive backend (idempotent)."""

from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.infrastructure.database.postgres import PostgresDatabase

logger = logging.getLogger(__name__)


async def seed() -> None:
    settings = get_settings()
    db = PostgresDatabase(settings)
    await db.connect()

    try:
        await db.execute(
            """
            INSERT INTO customer_profiles (customer_id, email, first_name, last_name)
            VALUES ('demo_customer_001', 'demo@thinkfive.ai', 'Demo', 'Customer')
            ON CONFLICT (customer_id) DO NOTHING
            """
        )

        await db.execute(
            """
            INSERT INTO customer_cards (card_id, customer_id, card_last_four, card_brand, card_type, is_primary)
            VALUES ('card_demo_001', 'demo_customer_001', '1234', 'VISA', 'DEBIT', TRUE)
            ON CONFLICT (card_id) DO NOTHING
            """
        )

        await db.execute(
            """
            INSERT INTO app_users (email, role, customer_id, hashed_password, is_active)
            VALUES ('demo@thinkfive.ai', 'CUSTOMER', 'demo_customer_001',
                    '$2b$12$ug0GbmCtlhFDk9JEGOWD0ujC3BogvQhOsPcxyTnXRLSN/U8kxypoG', TRUE)
            ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
            """
        )
        await db.execute(
            """
            INSERT INTO app_users (email, role, hashed_password, is_active)
            VALUES ('analyst@thinkfive.ai', 'ANALYST',
                    '$2b$12$NafccG65kpW7LzK9Y/F08uqYhrdsHYuHkru6KMDGD5LUdFN9ku6bW', TRUE)
            ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
            """
        )
        await db.execute(
            """
            INSERT INTO app_users (email, role, hashed_password, is_active)
            VALUES ('supervisor@thinkfive.ai', 'SUPERVISOR',
                    '$2b$12$fzzS7LTiuNTwxZGiwMgGFOUBU0xrpp5scSccZoAaz86NfCuporMZe', TRUE)
            ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
            """
        )
        await db.execute(
            """
            INSERT INTO app_users (email, role, hashed_password, is_active)
            VALUES ('admin@thinkfive.ai', 'ADMIN',
                    '$2b$12$SegobeOZAaIqwRa7RacoGOR.EMgPiwCMVnz5jo5AZLfYZ6r17tRzy', TRUE)
            ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
            """
        )

        # Default agent configurations with safety ceilings enforced in code, not DB.
        for agent_name in ("supervisor", "banking", "fraud", "knowledge", "case", "synthesis"):
            await db.execute(
                """
                INSERT INTO agent_configs (agent_name, enabled, provider, model, temperature, max_iterations)
                VALUES ($1, TRUE, 'openai', 'gemini-3-flash-preview', 0.0, 15)
                ON CONFLICT (agent_name) DO NOTHING
                """,
                agent_name,
            )

        logger.info("Demo data seeded successfully")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
