"""Health check routers."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "healthy", "service": "thinkfive-backend"}


@router.get("/ready")
async def ready(request: Request) -> dict[str, object]:
    """Readiness check - verifies database connectivity."""
    container = getattr(request.app.state, "container", None)
    if container is None:
        return {"status": "not_ready", "reason": "container not initialized"}

    db_healthy = await container.db.health_check()
    return {
        "status": "ready" if db_healthy else "not_ready",
        "database": db_healthy,
    }
