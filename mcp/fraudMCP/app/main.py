from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

from fraudMCP.app.config import Settings, get_settings
from fraudMCP.app.container import Container, create_container
from fraudMCP.app.logging import configure_logging
from fraudMCP.app.mcp.server import create_fraud_mcp as _create_fraud_mcp
from fraudMCP.app.security import BearerTokenMiddleware


def create_fraud_mcp(settings: Settings | None = None, container: Container | None = None) -> FastMCP:
    resolved_settings = settings or get_settings()
    resolved_container = container or create_container(resolved_settings)
    return _create_fraud_mcp(resolved_container)


def create_fraud_asgi_app(
    settings: Settings | None = None,
    container: Container | None = None,
    *,
    mount_path: str | None = None,
) -> FastAPI:
    """Create a standalone ASGI app without binding a port or creating import-time state."""
    resolved_settings = settings or get_settings()
    resolved_container = container or create_container(resolved_settings)
    path = mount_path or resolved_settings.fraud_mcp_mount_path
    if path != "/":
        path = path.rstrip("/")

    fraud_mcp = _create_fraud_mcp(resolved_container)
    mcp_app = fraud_mcp.http_app(path="/")
    token = resolved_settings.mcp_auth_token.get_secret_value() if resolved_settings.mcp_auth_token else None
    protected_mcp_app = BearerTokenMiddleware(mcp_app, token)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with mcp_app.lifespan(app):
            yield

    app = FastAPI(title="Fraud MCP", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.fraud_container = resolved_container
    app.state.fraud_mcp = fraud_mcp
    app.mount(path, cast(Any, protected_mcp_app))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": "fraud-mcp"}

    @app.get("/ready")
    async def ready() -> JSONResponse:
        details = resolved_settings.safe_summary()
        is_ready = bool(details["banking_provider_configured"] and (details["repository_backend"] == "memory" or details["supabase_configured"]))
        return JSONResponse({"status": "ready" if is_ready else "not_ready", "checks": details}, status_code=200 if is_ready else 503)

    return app


def create_app() -> FastAPI:
    configure_logging()
    return create_fraud_asgi_app()
