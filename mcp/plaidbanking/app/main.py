from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from common.supabase import create_data_client
from plaidbanking.app.config import Settings, get_settings
from plaidbanking.app.container import Container, create_container
from plaidbanking.app.logging import configure_logging
from plaidbanking.app.mcp import create_banking_mcp
from plaidbanking.app.security import BearerTokenMiddleware
from plaidbanking.app.webhook import create_webhook_router


def create_banking_asgi_app(settings: Settings | None = None, container: Container | None = None, *, mount_path: str | None = None) -> FastAPI:
    """Create a standalone ASGI app without binding a port or creating import-time state."""
    resolved_settings = settings or get_settings()
    if container is not None:
        resolved_container = container
    elif resolved_settings.banking_data_provider == "supabase":
        if not resolved_settings.supabase_url:
            raise ValueError("SUPABASE_URL is required when BANKING_DATA_PROVIDER=supabase")
        client = create_data_client(resolved_settings.supabase_url, resolved_settings.service_key.get_secret_value())
        resolved_container = create_container(resolved_settings, supabase_client=client)
    else:
        resolved_container = create_container(resolved_settings)
    path = (mount_path or resolved_settings.plaid_mcp_mount_path).rstrip("/")
    banking_mcp = create_banking_mcp(resolved_container)
    mcp_app = banking_mcp.http_app(path="/")
    token = resolved_settings.mcp_auth_token.get_secret_value() if resolved_settings.mcp_auth_token else None
    protected_mcp_app = BearerTokenMiddleware(mcp_app, token)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with mcp_app.lifespan(app):
            if resolved_settings.banking_data_provider == "plaid" and resolved_settings.plaid_auto_bootstrap and resolved_container.bootstrap is not None:
                await resolved_container.bootstrap.bootstrap()
            yield

    app = FastAPI(title="ThinkFive Banking MCP", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.banking_container = resolved_container
    app.state.banking_mcp = banking_mcp
    app.include_router(create_webhook_router(resolved_container))
    app.mount(path, protected_mcp_app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": "thinkfive-banking-mcp"}

    @app.get("/ready")
    async def ready() -> JSONResponse:
        details = resolved_settings.safe_summary()
        is_ready = bool(
            details["supabase_configured"]
            if resolved_settings.banking_data_provider == "supabase"
            else details["client_id_configured"] and details["secret_configured"]
        )
        return JSONResponse({"status": "ready" if is_ready else "not_ready", "checks": details}, status_code=200 if is_ready else 503)

    return app


def create_app() -> FastAPI:
    configure_logging()
    return create_banking_asgi_app()
