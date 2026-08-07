from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MCP_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(MCP_ENV, ".env"), extra="ignore", case_sensitive=True)
    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_service_role_key: SecretStr | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_secret_key: SecretStr | None = Field(default=None, alias="SUPABASE_SECRET_KEY")
    supabase_db_url: SecretStr | None = Field(default=None, alias="SUPABASE_DB_URL")
    mcp_auth_token: SecretStr | None = Field(default=None, alias="MCP_AUTH_TOKEN")
    mcp_provider_mode: Literal["local", "remote"] = Field(default="local", alias="MCP_PROVIDER_MODE")
    banking_mcp_url: str | None = Field(default=None, alias="BANKING_MCP_URL")
    banking_mcp_auth_token: SecretStr | None = Field(default=None, alias="BANKING_MCP_AUTH_TOKEN")
    fraud_mcp_url: str | None = Field(default=None, alias="FRAUD_MCP_URL")
    fraud_mcp_auth_token: SecretStr | None = Field(default=None, alias="FRAUD_MCP_AUTH_TOKEN")
    case_mcp_mount_path: str = Field(default="/mcp", alias="CASE_MCP_MOUNT_PATH")
    case_auto_migrate: bool = Field(default=False, alias="CASE_AUTO_MIGRATE")
    case_auto_seed: bool = Field(default=False, alias="CASE_AUTO_SEED")
    case_enforce_rbac: bool = Field(default=True, alias="CASE_ENFORCE_RBAC")
    repository_backend: Literal["supabase", "memory"] = Field(default="supabase", alias="CASE_REPOSITORY_BACKEND")

    @property
    def service_key(self) -> SecretStr:
        key = self.supabase_service_role_key or self.supabase_secret_key
        if key is None:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SECRET_KEY is required")
        return key

    @field_validator("case_mcp_mount_path")
    @classmethod
    def mount_path(cls, value: str) -> str:
        if not value.startswith("/") or value == "/" or "//" in value:
            raise ValueError("CASE_MCP_MOUNT_PATH must be an absolute non-root path")
        return value.rstrip("/")

    def safe_summary(self) -> dict[str, object]:
        return {
            "supabase_configured": bool(self.supabase_url and self.service_key.get_secret_value()),
            "banking_provider_configured": self.mcp_provider_mode == "local" or bool(self.banking_mcp_url),
            "fraud_provider_configured": self.mcp_provider_mode == "local" or bool(self.fraud_mcp_url),
            "provider_mode": self.mcp_provider_mode,
            "repository_backend": self.repository_backend,
            "mount_path": self.case_mcp_mount_path,
        }
