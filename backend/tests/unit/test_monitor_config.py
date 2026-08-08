from __future__ import annotations

import pytest

from app.core.config import Settings


def settings_with_monitor_ids(value: str) -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql://user:password@localhost:5432/postgres",
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SECRET_KEY="secret",
        SUPABASE_SERVICE_ROLE_KEY="service-role",
        SUPABASE_PUBLISHABLE_KEY="publishable",
        MCP_BASE_URL="https://mcp.example.com",
        MCP_AUTH_TOKEN="mcp-token",
        MONITOR_CUSTOMER_IDS=value,
    )


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (
            '["demo_customer_001", "demo_customer_002"]',
            ["demo_customer_001", "demo_customer_002"],
        ),
        (
            "demo_customer_001,demo_customer_002",
            ["demo_customer_001", "demo_customer_002"],
        ),
        (
            " demo_customer_001, demo_customer_001 ",
            ["demo_customer_001"],
        ),
    ],
)
def test_monitor_customer_ids_accept_render_formats(
    configured: str, expected: list[str]
) -> None:
    assert settings_with_monitor_ids(configured).monitor_customer_ids == expected


def test_monitor_customer_ids_reject_empty_configuration() -> None:
    with pytest.raises(ValueError, match="at least one customer ID"):
        _ = settings_with_monitor_ids("[]").monitor_customer_ids


def test_monitor_defaults_cover_both_demo_customers_every_thirty_seconds() -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://user:password@localhost:5432/postgres",
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SECRET_KEY="secret",
        SUPABASE_SERVICE_ROLE_KEY="service-role",
        SUPABASE_PUBLISHABLE_KEY="publishable",
        MCP_BASE_URL="https://mcp.example.com",
        MCP_AUTH_TOKEN="mcp-token",
    )

    assert settings.monitor_enabled is True
    assert settings.monitor_interval_seconds == 30
    assert settings.monitor_customer_ids == ["demo_customer_001", "demo_customer_002"]
