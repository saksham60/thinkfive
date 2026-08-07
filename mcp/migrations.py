from __future__ import annotations

from pathlib import Path

from case.app.config import Settings as CaseSettings

MIGRATIONS = (
    Path(__file__).parent / "fraudMCP/app/database/migrations/001_fraud_mcp.sql",
    Path(__file__).parent / "case/app/database/migrations/001_case_mcp.sql",
)


def apply_all_migrations(settings: CaseSettings) -> None:
    import psycopg

    if not settings.supabase_db_url:
        raise RuntimeError("SUPABASE_DB_URL is required to apply combined MCP migrations")
    with psycopg.connect(settings.supabase_db_url.get_secret_value(), autocommit=True) as connection:
        for migration in MIGRATIONS:
            connection.execute(migration.read_text(encoding="utf-8"))
