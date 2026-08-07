from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).with_name(".env")


class CombinedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_ENV, env_file_encoding="utf-8", extra="ignore", case_sensitive=True)

    provider_mode: Literal["local", "remote"] = Field(default="local", alias="MCP_PROVIDER_MODE")
    mcp_auth_token: SecretStr | None = Field(default=None, alias="MCP_AUTH_TOKEN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    auto_migrate: bool = Field(default=False, alias="MCP_AUTO_MIGRATE")

    @property
    def auth_token(self) -> str | None:
        return self.mcp_auth_token.get_secret_value() if self.mcp_auth_token else None
