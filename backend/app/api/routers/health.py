"""Health check routers."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "healthy", "service": "thinkfive-backend"}


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    """Readiness check - verifies database connectivity."""
    container = getattr(request.app.state, "container", None)
    if container is None:
        return JSONResponse({"status": "not_ready", "reason": "container not initialized"}, status_code=503)

    db_healthy = await container.db.health_check()
    checkpoint_ready = container.checkpointer_factory._saver is not None
    mcp_ready = container.mcp_manager.initialized
    is_ready = db_healthy and checkpoint_ready and mcp_ready
    return JSONResponse({
        "status": "ready" if is_ready else "not_ready",
        "database": db_healthy,
        "checkpointer": checkpoint_ready,
        "mcp": mcp_ready,
    }, status_code=200 if is_ready else 503)
