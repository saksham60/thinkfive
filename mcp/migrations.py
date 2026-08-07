from __future__ import annotations

import ssl
from pathlib import Path
from urllib.parse import urlparse

import httpx
import truststore

from case.app.config import Settings as CaseSettings

MIGRATIONS = (
    Path(__file__).parent / "fraudMCP/app/database/migrations/001_fraud_mcp.sql",
    Path(__file__).parent / "case/app/database/migrations/001_case_mcp.sql",
)


def apply_all_migrations(settings: CaseSettings) -> None:
    if settings.supabase_db_url:
        _apply_with_postgres(settings)
        return
    if settings.supabase_access_token:
        _apply_with_management_api(settings)
        return
    raise RuntimeError("SUPABASE_DB_URL or SUPABASE_ACCESS_TOKEN is required to apply combined MCP migrations")


def _apply_with_postgres(settings: CaseSettings) -> None:
    import psycopg

    assert settings.supabase_db_url is not None
    with psycopg.connect(settings.supabase_db_url.get_secret_value(), autocommit=True) as connection:
        for migration in MIGRATIONS:
            connection.execute(migration.read_text(encoding="utf-8"))


def _apply_with_management_api(settings: CaseSettings) -> None:
    assert settings.supabase_access_token is not None
    host = urlparse(settings.supabase_url).hostname or ""
    project_ref = host.split(".", 1)[0]
    if not project_ref or not host.endswith(".supabase.co"):
        raise RuntimeError("SUPABASE_URL does not contain a valid hosted project reference")
    endpoint = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
    headers = {"Authorization": f"Bearer {settings.supabase_access_token.get_secret_value()}"}
    context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    with httpx.Client(headers=headers, timeout=60, trust_env=False, verify=context) as client:
        for migration in MIGRATIONS:
            response = client.post(endpoint, json={"query": migration.read_text(encoding="utf-8")})
            response.raise_for_status()
