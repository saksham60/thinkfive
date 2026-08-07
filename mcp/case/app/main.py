from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from case.app.config import Settings
from case.app.container import Container, create_container
from case.app.database import apply_case_migrations
from case.app.mcp import create_case_mcp
from case.app.models.domain import CardState
from case.app.security import BearerTokenMiddleware


def create_case_asgi_app(settings: Settings | None = None, container: Container | None = None, *, mount_path: str | None = None) -> FastAPI:
    s = settings or Settings()
    c = container or create_container(s)
    m = create_case_mcp(c)
    mcp_app = m.http_app(path="/")
    token = s.mcp_auth_token.get_secret_value() if s.mcp_auth_token else None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with mcp_app.lifespan(app):
            if s.case_auto_migrate:
                await asyncio.to_thread(apply_case_migrations, s)
            if s.case_auto_seed:
                await c.cards.upsert(CardState(card_id="card_demo_001", customer_id="demo_customer_001", updated_by="seed_demo_data"))
            yield

    app = FastAPI(title="Case MCP", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.container = c
    app.mount((mount_path or s.case_mcp_mount_path).rstrip("/"), BearerTokenMiddleware(mcp_app, token))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": "case-mcp"}

    @app.get("/ready")
    async def ready() -> JSONResponse:
        checks = s.safe_summary()
        ok = bool(checks["supabase_configured"] or s.repository_backend == "memory")
        return JSONResponse({"status": "ready" if ok else "not_ready", "checks": checks}, status_code=200 if ok else 503)

    return app


def create_app() -> FastAPI:
    return create_case_asgi_app()
