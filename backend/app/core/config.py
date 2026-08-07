"""Application configuration."""

from __future__ import annotations

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
    debug: bool = False
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
    cookie_samesite: str = "lax"

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

    # LLM Provider
    llm_provider: Literal["openai", "gemini"] = "openai"
    openai_api_key: SecretStr = Field(..., validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(..., validation_alias="OPENAI_BASE_URL")
    openai_model: str = Field("gemini-3-flash-preview", validation_alias="OPENAI_MODEL")
    litellm_base_url: str = Field(..., validation_alias="LITELLM_BASE_URL")
    litellm_api_key: SecretStr = Field(..., validation_alias="LITELLM_API_KEY")
    litellm_model: str = Field("gemini-3-flash-preview", validation_alias="LITELLM_MODEL")
    gemini_model: str = Field("gemini-3-flash-preview", validation_alias="GEMINI_MODEL")

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
    embedding_provider: Literal["openai"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

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
    monitor_enabled: bool = True
    monitor_interval_seconds: int = 300  # 5 minutes
    monitor_customer_ids: list[str] = ["demo_customer_001"]

    # SSE
    sse_heartbeat_interval: int = 30  # seconds
    sse_max_event_age: int = 3600  # 1 hour for replay


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()  # type: ignore[call-arg]
