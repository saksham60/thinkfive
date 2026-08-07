from __future__ import annotations

from pathlib import Path

from case.app.config import Settings


def apply_case_migrations(settings: Settings) -> None:
    import psycopg

    if not settings.supabase_db_url:
        raise RuntimeError("SUPABASE_DB_URL is required to apply Case MCP migrations")
    migration = Path(__file__).with_name("migrations") / "001_case_mcp.sql"
    with psycopg.connect(settings.supabase_db_url.get_secret_value(), autocommit=True) as connection:
        connection.execute(migration.read_text(encoding="utf-8"))
