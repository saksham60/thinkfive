"""FastAPI application entrypoint with lifespan management."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    alerts,
    approvals,
    auth,
    cases,
    chat,
    customers,
    evaluation,
    events,
    health,
    policies,
    simulator,
    supervisor,
)
from app.bootstrap import create_container
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup validates config, initializes infra; shutdown closes it."""
    settings = get_settings()
    configure_logging(settings.log_level)

    container = create_container(settings)
    app.state.container = container

    await container.startup()

    # Transaction monitor as a background asyncio task (not a separate process/service)
    monitor_task = None
    monitor_status = {
        "enabled": settings.monitor_enabled,
        "running": False,
        "interval_seconds": settings.monitor_interval_seconds,
        "customer_ids": settings.monitor_customer_ids,
        "last_started_at": None,
        "last_completed_at": None,
        "last_results": {},
        "last_errors": {},
    }
    app.state.monitor_status = monitor_status
    if settings.monitor_enabled:
        import asyncio

        async def _monitor_loop() -> None:
            monitor_status["running"] = True
            logger.info(
                "Transaction monitor started: interval=%ss customers=%s",
                settings.monitor_interval_seconds,
                settings.monitor_customer_ids,
            )
            try:
                while True:
                    monitor_status["last_started_at"] = datetime.now(UTC).isoformat()
                    cycle_results: dict[str, object] = {}
                    cycle_errors: dict[str, str] = {}
                    for customer_id in settings.monitor_customer_ids:
                        try:
                            cycle_results[customer_id] = (
                                await container.monitor_transactions_use_case.execute(customer_id)
                            )
                        except Exception as exc:
                            error_code = str(getattr(exc, "code", type(exc).__name__))
                            cycle_errors[customer_id] = error_code
                            logger.exception(
                                "Transaction monitor failed for %s [%s]",
                                customer_id,
                                error_code,
                            )
                    monitor_status["last_results"] = cycle_results
                    monitor_status["last_errors"] = cycle_errors
                    monitor_status["last_completed_at"] = datetime.now(UTC).isoformat()
                    logger.info(
                        "Transaction monitor cycle complete: results=%s errors=%s",
                        cycle_results,
                        cycle_errors,
                    )
                    await asyncio.sleep(settings.monitor_interval_seconds)
            finally:
                monitor_status["running"] = False

        monitor_task = asyncio.create_task(_monitor_loop())

    try:
        yield
    finally:
        if monitor_task:
            monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await monitor_task
        await container.shutdown()


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    app = FastAPI(
        title="ThinkFive Backend",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_allowed_origin_regex,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "Last-Event-ID"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(events.router)
    app.include_router(customers.router)
    app.include_router(alerts.router)
    app.include_router(cases.router)
    app.include_router(approvals.router)
    app.include_router(supervisor.router)
    app.include_router(policies.router)
    app.include_router(policies.system_router)
    app.include_router(simulator.router)
    app.include_router(evaluation.router)

    return app


app = create_app()
