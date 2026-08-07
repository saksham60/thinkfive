"""FastAPI application entrypoint with lifespan management."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

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
    if settings.monitor_enabled:
        import asyncio

        async def _monitor_loop() -> None:
            while True:
                for customer_id in settings.monitor_customer_ids:
                    try:
                        await container.monitor_transactions_use_case.execute(customer_id)
                    except Exception as e:
                        logger.error(f"Transaction monitor failed for {customer_id}: {e}")
                await asyncio.sleep(settings.monitor_interval_seconds)

        monitor_task = asyncio.create_task(_monitor_loop())

    try:
        yield
    finally:
        if monitor_task:
            monitor_task.cancel()
        await container.shutdown()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="ThinkFive Backend",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
