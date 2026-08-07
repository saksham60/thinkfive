from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
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

    mcp_provider_mode: Literal["local", "remote"] = Field(default="local", alias="MCP_PROVIDER_MODE")
    banking_mcp_url: str | None = Field(default=None, alias="BANKING_MCP_URL")
    banking_mcp_auth_token: SecretStr | None = Field(default=None, alias="BANKING_MCP_AUTH_TOKEN")
    mcp_auth_token: SecretStr | None = Field(default=None, alias="MCP_AUTH_TOKEN")
    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_service_role_key: SecretStr | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_secret_key: SecretStr | None = Field(default=None, alias="SUPABASE_SECRET_KEY")
    fraud_repository_backend: Literal["supabase", "memory"] = Field(default="supabase", alias="FRAUD_REPOSITORY_BACKEND")

    fraud_mcp_mount_path: str = Field(default="/mcp", alias="FRAUD_MCP_MOUNT_PATH")
    fraud_history_limit: int = Field(default=100, alias="FRAUD_HISTORY_LIMIT", ge=1, le=200)
    fraud_assessment_max_batch: int = Field(default=100, alias="FRAUD_ASSESSMENT_MAX_BATCH", ge=1, le=200)
    fraud_max_alert_results: int = Field(default=100, alias="FRAUD_MAX_ALERT_RESULTS", ge=1, le=200)
    fraud_max_concurrent_assessments: int = Field(default=20, alias="FRAUD_MAX_CONCURRENT_ASSESSMENTS", ge=1, le=100)

    fraud_alert_threshold: float = Field(default=0.65, alias="FRAUD_ALERT_THRESHOLD", ge=0.0, le=1.0)
    fraud_medium_threshold: float = Field(default=0.35, alias="FRAUD_MEDIUM_THRESHOLD", ge=0.0, le=1.0)
    fraud_high_threshold: float = Field(default=0.65, alias="FRAUD_HIGH_THRESHOLD", ge=0.0, le=1.0)
    fraud_critical_threshold: float = Field(default=0.85, alias="FRAUD_CRITICAL_THRESHOLD", ge=0.0, le=1.0)

    fraud_enable_isolation_forest: bool = Field(default=True, alias="FRAUD_ENABLE_ISOLATION_FOREST")
    fraud_min_model_history: int = Field(default=30, alias="FRAUD_MIN_MODEL_HISTORY", ge=10, le=500)
    fraud_isolation_forest_random_state: int = Field(default=42, alias="FRAUD_ISOLATION_FOREST_RANDOM_STATE")

    banking_provider_timeout_seconds: float = Field(default=10.0, alias="BANKING_PROVIDER_TIMEOUT_SECONDS", gt=0.1, le=60)
    banking_provider_max_retries: int = Field(default=2, alias="BANKING_PROVIDER_MAX_RETRIES", ge=0, le=5)
    banking_provider_max_backoff_seconds: float = Field(default=2.0, alias="BANKING_PROVIDER_MAX_BACKOFF_SECONDS", ge=0.1, le=30)

    fraud_weight_amount_anomaly: float = Field(default=0.24, alias="FRAUD_WEIGHT_AMOUNT_ANOMALY", ge=0.0, le=1.0)
    fraud_weight_velocity: float = Field(default=0.18, alias="FRAUD_WEIGHT_VELOCITY", ge=0.0, le=1.0)
    fraud_weight_merchant_novelty: float = Field(default=0.14, alias="FRAUD_WEIGHT_MERCHANT_NOVELTY", ge=0.0, le=1.0)
    fraud_weight_category_novelty: float = Field(default=0.10, alias="FRAUD_WEIGHT_CATEGORY_NOVELTY", ge=0.0, le=1.0)
    fraud_weight_location_anomaly: float = Field(default=0.10, alias="FRAUD_WEIGHT_LOCATION_ANOMALY", ge=0.0, le=1.0)
    fraud_weight_account_balance_context: float = Field(default=0.10, alias="FRAUD_WEIGHT_ACCOUNT_BALANCE_CONTEXT", ge=0.0, le=1.0)
    fraud_weight_device_risk: float = Field(default=0.08, alias="FRAUD_WEIGHT_DEVICE_RISK", ge=0.0, le=1.0)
    fraud_weight_blacklist_risk: float = Field(default=0.06, alias="FRAUD_WEIGHT_BLACKLIST_RISK", ge=0.0, le=1.0)

    fraud_velocity_window_hours: int = Field(default=24, alias="FRAUD_VELOCITY_WINDOW_HOURS", ge=1, le=168)
    fraud_velocity_count_high: int = Field(default=6, alias="FRAUD_VELOCITY_COUNT_HIGH", ge=2, le=100)
    fraud_velocity_amount_multiplier_high: float = Field(default=4.0, alias="FRAUD_VELOCITY_AMOUNT_MULTIPLIER_HIGH", ge=1.0, le=100.0)

    @field_validator("fraud_mcp_mount_path")
    @classmethod
    def validate_mount_path(cls, value: str) -> str:
        if not value.startswith("/") or "//" in value:
            raise ValueError("FRAUD_MCP_MOUNT_PATH must be an absolute path")
        if value != "/" and value.endswith("/"):
            return value.rstrip("/")
        return value

    @field_validator("banking_mcp_url")
    @classmethod
    def validate_banking_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            return None
        if not trimmed.startswith("http://") and not trimmed.startswith("https://"):
            raise ValueError("BANKING_MCP_URL must start with http:// or https://")
        return trimmed.rstrip("/")

    @model_validator(mode="after")
    def validate_thresholds(self) -> Settings:
        if not (0.0 <= self.fraud_medium_threshold < self.fraud_high_threshold < self.fraud_critical_threshold <= 1.0):
            raise ValueError("severity thresholds must satisfy 0 <= medium < high < critical <= 1")
        if not (0.0 <= self.fraud_alert_threshold <= 1.0):
            raise ValueError("FRAUD_ALERT_THRESHOLD must be between 0 and 1")
        if sum(self.feature_weights().values()) <= 0:
            raise ValueError("at least one feature weight must be greater than zero")
        return self

    @property
    def service_key(self) -> SecretStr:
        key = self.supabase_service_role_key or self.supabase_secret_key
        if key is None:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for Supabase fraud persistence")
        return key

    def feature_weights(self) -> dict[str, float]:
        return {
            "amount_anomaly": self.fraud_weight_amount_anomaly,
            "velocity": self.fraud_weight_velocity,
            "merchant_novelty": self.fraud_weight_merchant_novelty,
            "category_novelty": self.fraud_weight_category_novelty,
            "location_anomaly": self.fraud_weight_location_anomaly,
            "account_balance_context": self.fraud_weight_account_balance_context,
            "device_risk": self.fraud_weight_device_risk,
            "blacklist_risk": self.fraud_weight_blacklist_risk,
        }

    def safe_summary(self) -> dict[str, object]:
        return {
            "provider_mode": self.mcp_provider_mode,
            "banking_provider_configured": self.mcp_provider_mode == "local" or bool(self.banking_mcp_url),
            "repository_backend": self.fraud_repository_backend,
            "supabase_configured": bool(self.supabase_url and (self.supabase_service_role_key or self.supabase_secret_key)),
            "mount_path": self.fraud_mcp_mount_path,
            "history_limit": self.fraud_history_limit,
            "alert_threshold": self.fraud_alert_threshold,
            "severity_thresholds": {
                "medium": self.fraud_medium_threshold,
                "high": self.fraud_high_threshold,
                "critical": self.fraud_critical_threshold,
            },
            "enable_isolation_forest": self.fraud_enable_isolation_forest,
            "banking_auth_configured": bool(self.banking_mcp_auth_token and self.banking_mcp_auth_token.get_secret_value()),
            "mcp_auth_configured": bool(self.mcp_auth_token and self.mcp_auth_token.get_secret_value()),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
