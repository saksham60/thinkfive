from __future__ import annotations

import pytest
from pydantic import ValidationError

from plaidbanking.app.config import Settings


def test_missing_client_id_fails() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, PLAID_SECRET="secret")


def test_missing_secret_fails() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, PLAID_CLIENT_ID="client")


def test_invalid_environment_fails() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, PLAID_CLIENT_ID="client", PLAID_SECRET="secret", PLAID_ENV="invalid")


def test_valid_config_and_mount_path() -> None:
    settings = Settings(_env_file=None, PLAID_CLIENT_ID="client", PLAID_SECRET="secret", PLAID_MCP_MOUNT_PATH="/mcp/banking/")
    assert settings.plaid_mcp_mount_path == "/mcp/banking"
    assert "PLAID_SECRET=secret" not in str(settings)
    assert "'secret'" not in str(settings.safe_summary())


@pytest.mark.parametrize("path", ["mcp", "/", "//mcp"])
def test_invalid_mount_path(path: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, PLAID_CLIENT_ID="client", PLAID_SECRET="secret", PLAID_MCP_MOUNT_PATH=path)
