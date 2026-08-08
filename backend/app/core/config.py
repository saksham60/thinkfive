"""Application configuration."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "thinkfive-backend"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(False, validation_alias="APP_DEBUG")
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False

    # Auth
    auth_mode: Literal["demo", "supabase"] = "demo"
    session_secret: str = "insecure-demo-secret-change-in-production"
    session_cookie_name: str = "thinkfive_session"
    session_max_age: int = 86400  # 24 hours
    cookie_secure: bool = False  # Set true in production with HTTPS
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # Browser clients. Credentialed requests cannot use a wildcard origin.
    cors_allowed_origins: str = Field(
        "http://localhost:5173,http://localhost:3000",
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    cors_allowed_origin_regex: str | None = Field(
        None,
        validation_alias="CORS_ALLOWED_ORIGIN_REGEX",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return the configured, non-empty browser origins."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    # Database (direct PostgreSQL connection string)
    database_url: str = Field(
        ...,
        validation_alias="DATABASE_URL",
        description="PostgreSQL DSN used by asyncpg, migrations, and LangGraph",
    )
    supabase_url: str = Field(..., validation_alias="SUPABASE_URL")
    supabase_secret_key: SecretStr = Field(..., validation_alias="SUPABASE_SECRET_KEY")
    supabase_service_role_key: SecretStr = Field(..., validation_alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_publishable_key: str = Field(..., validation_alias="SUPABASE_PUBLISHABLE_KEY")
    supabase_jwks_url: str | None = Field(None, validation_alias="SUPABASE_JWKS_URL")

    # LLM providers. Chat and embeddings are selected independently so either
    # can be moved between LiteLLM and Google without code changes.
    llm_provider: Literal["litellm", "gemini", "openai"] = Field(
        "litellm", validation_alias="LLM_PROVIDER"
    )
    litellm_base_url: str | None = Field(None, validation_alias="LITELLM_BASE_URL")
    litellm_api_key: SecretStr | None = Field(None, validation_alias="LITELLM_API_KEY")
    litellm_team_id: str | None = Field(None, validation_alias="LITELLM_TEAM_ID")
    litellm_model: str = Field("gemini-3-flash-preview", validation_alias="LITELLM_MODEL")
    gemini_api_key: SecretStr | None = Field(None, validation_alias="GEMINI_API_KEY")
    gemini_base_url: str = Field(
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        validation_alias="GEMINI_BASE_URL",
    )
    gemini_model: str = Field("gemini-flash-latest", validation_alias="GEMINI_MODEL")

    # LangSmith Tracing
    langsmith_api_key: SecretStr | None = Field(None, validation_alias="LANGSMITH_API_KEY")
    langsmith_tracing: bool = Field(False, validation_alias="LANGSMITH_TRACING")
    langsmith_project: str = Field("thinkfive-backend", validation_alias="LANGSMITH_PROJECT")

    # MCP Services
    mcp_base_url: str = Field(..., validation_alias="MCP_BASE_URL")
    mcp_auth_token: SecretStr = Field(..., validation_alias="MCP_AUTH_TOKEN")
    mcp_timeout: int = 60
    mcp_max_retries: int = 3

    @property
    def banking_mcp_url(self) -> str:
        return f"{self.mcp_base_url.rstrip('/')}/mcp/banking"

    @property
    def fraud_mcp_url(self) -> str:
        return f"{self.mcp_base_url.rstrip('/')}/mcp/fraud"

    @property
    def case_mcp_url(self) -> str:
        return f"{self.mcp_base_url.rstrip('/')}/mcp/case"

    # Embeddings
    embedding_provider: Literal["litellm", "gemini"] = Field(
        "litellm", validation_alias="EMBEDDING_PROVIDER"
    )
    litellm_embedding_model: str = Field(
        "text-embedding-3-small", validation_alias="LITELLM_EMBEDDING_MODEL"
    )
    gemini_embedding_model: str = Field(
        "gemini-embedding-2", validation_alias="GEMINI_EMBEDDING_MODEL"
    )
    embedding_dimensions: int = Field(1536, validation_alias="EMBEDDING_DIMENSIONS")

    # Memory
    memory_summary_threshold: int = 20  # messages before summarization
    memory_recent_messages: int = 10  # recent messages to keep in prompt
    customer_memory_ttl_days: int = 90  # days before memory expires

    # HITL
    hitl_enabled: bool = True
    hitl_timeout_minutes: int = 60

    # Graph
    graph_max_iterations: int = 15
    graph_recursion_limit: int = 25

    # RAG
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.7

    # Transaction Monitor
    monitor_enabled: bool = Field(True, validation_alias="MONITOR_ENABLED")
    monitor_interval_seconds: int = Field(
        30, validation_alias="MONITOR_INTERVAL_SECONDS", ge=5
    )
    monitor_customer_ids_raw: str = Field(
        '["demo_customer_001","demo_customer_002"]',
        validation_alias="MONITOR_CUSTOMER_IDS",
    )

    @property
    def monitor_customer_ids(self) -> list[str]:
        """Accept Render's JSON-array format and a forgiving comma-separated fallback."""
        raw = self.monitor_customer_ids_raw.strip()
        values: list[str]
        try:
            decoded = json.loads(raw)
            values = decoded if isinstance(decoded, list) else [str(decoded)]
        except json.JSONDecodeError:
            values = raw.split(",")

        customer_ids = list(
            dict.fromkeys(str(value).strip() for value in values if str(value).strip())
        )
        if not customer_ids:
            raise ValueError("MONITOR_CUSTOMER_IDS must contain at least one customer ID")
        return customer_ids

    # SSE
    sse_heartbeat_interval: int = 30  # seconds
    sse_max_event_age: int = 3600  # 1 hour for replay


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()  # type: ignore[call-arg]
