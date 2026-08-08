"""Database migration runner."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path

import asyncpg

from app.core.config import get_settings

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


async def get_connection() -> asyncpg.Connection:
    """Get database connection."""
    settings = get_settings()
    return await asyncpg.connect(settings.database_url)


async def get_applied_migrations(conn: asyncpg.Connection) -> set[str]:
    """Get set of already-applied migration IDs."""
    # Ensure migrations table exists
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS backend_schema_migrations (
            migration_id TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            checksum TEXT,
            description TEXT
        )
        """
    )

    rows = await conn.fetch("SELECT migration_id FROM backend_schema_migrations")
    return {row["migration_id"] for row in rows}


def get_migration_checksum(content: str) -> str:
    """Calculate migration checksum."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


async def apply_migration(conn: asyncpg.Connection, migration_file: Path) -> None:
    """Apply a single migration file."""
    migration_id = migration_file.stem
    content = migration_file.read_text()
    checksum = get_migration_checksum(content)

    logger.info(f"Applying migration: {migration_id}")

    try:
        async with conn.transaction():
            # Execute migration SQL
            await conn.execute(content)
            # Older migrations recorded themselves, while newer migrations rely
            # on the runner. Make the runner authoritative so every successful
            # migration is remembered and cannot rerun on every Render restart.
            await conn.execute(
                """
                INSERT INTO backend_schema_migrations
                    (migration_id, applied_at, checksum, description)
                VALUES ($1, NOW(), $2, $3)
                ON CONFLICT (migration_id) DO UPDATE
                    SET checksum = EXCLUDED.checksum,
                        description = EXCLUDED.description
                """,
                migration_id,
                checksum,
                migration_id.replace("_", " "),
            )

        logger.info(f"✓ Migration {migration_id} applied successfully")

    except Exception as e:
        logger.error(f"✗ Migration {migration_id} failed: {e}")
        raise


async def run_migrations() -> None:
    """Run all pending database migrations."""
    logger.info("Starting database migrations...")

    conn = await get_connection()
    try:
        applied = await get_applied_migrations(conn)
        logger.info(f"Found {len(applied)} already-applied migrations")

        # Get all migration files
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        pending = [f for f in migration_files if f.stem not in applied]

        if not pending:
            logger.info("✓ No pending migrations")
            return

        logger.info(f"Found {len(pending)} pending migrations")

        for migration_file in pending:
            await apply_migration(conn, migration_file)

        logger.info("✓ All migrations completed successfully")

    finally:
        await conn.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(run_migrations())
