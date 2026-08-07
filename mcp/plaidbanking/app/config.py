from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MCP_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # mcp/.env is the shared MCP configuration; a project-local .env can override it.
    model_config = SettingsConfigDict(
        env_file=(MCP_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    plaid_client_id: SecretStr = Field(alias="PLAID_CLIENT_ID")
    plaid_secret: SecretStr = Field(alias="PLAID_SECRET")
    plaid_env: Literal["sandbox", "development", "production"] = Field(default="sandbox", alias="PLAID_ENV")
    plaid_webhook_url: str | None = Field(default=None, alias="PLAID_WEBHOOK_URL")
    mcp_auth_token: SecretStr | None = Field(default=None, alias="MCP_AUTH_TOKEN")
    plaid_auto_bootstrap: bool = Field(default=True, alias="PLAID_AUTO_BOOTSTRAP")
    plaid_default_customer_id: str = Field(default="demo_customer_001", alias="PLAID_DEFAULT_CUSTOMER_ID")
    plaid_institution_id: str = Field(default="ins_109508", alias="PLAID_INSTITUTION_ID")
    plaid_mcp_mount_path: str = Field(default="/mcp", alias="PLAID_MCP_MOUNT_PATH")
    plaid_timeout_seconds: float = Field(default=10.0, alias="PLAID_TIMEOUT_SECONDS", gt=0, le=60)
    plaid_max_retries: int = Field(default=3, alias="PLAID_MAX_RETRIES", ge=0, le=5)
    webhook_replay_seconds: int = Field(default=300, alias="PLAID_WEBHOOK_REPLAY_SECONDS", ge=60, le=900)

    @field_validator("plaid_mcp_mount_path")
    @classmethod
    def validate_mount_path(cls, value: str) -> str:
        if not value.startswith("/") or value == "/" or "//" in value:
            raise ValueError("PLAID_MCP_MOUNT_PATH must be an absolute non-root path")
        return value.rstrip("/")

    @field_validator("plaid_default_customer_id", "plaid_institution_id")
    @classmethod
    def validate_nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value.strip()

    def safe_summary(self) -> dict[str, object]:
        return {
            "plaid_env": self.plaid_env,
            "mount_path": self.plaid_mcp_mount_path,
            "auto_bootstrap": self.plaid_auto_bootstrap,
            "client_id_configured": bool(self.plaid_client_id.get_secret_value()),
            "secret_configured": bool(self.plaid_secret.get_secret_value()),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
