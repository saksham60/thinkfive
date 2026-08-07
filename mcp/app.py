from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from case.app.config import Settings as CaseSettings
from case.app.container import Container as CaseContainer
from case.app.container import create_container as create_case_container
from case.app.mcp import create_case_mcp
from case.app.models.domain import CardState
from common.logging import configure_logging
from common.middleware import BearerTokenMiddleware, RequestIdMiddleware
from common.supabase import create_data_client
from config import CombinedSettings
from fraudMCP.app.config import Settings as FraudSettings
from fraudMCP.app.container import Container as FraudContainer
from fraudMCP.app.container import create_container as create_fraud_container
from fraudMCP.app.mcp.server import create_fraud_mcp
from migrations import apply_all_migrations
from plaidbanking.app.config import Settings as BankingSettings
from plaidbanking.app.container import Container as BankingContainer
from plaidbanking.app.container import create_container as create_banking_container
from plaidbanking.app.mcp import create_banking_mcp
from plaidbanking.app.plaid.client import PlaidGateway
from plaidbanking.app.webhook import create_webhook_router
from providers import LocalBankingDataProvider, LocalCaseBankingDataProvider, LocalFraudDataProvider


def _new_supabase_client(settings: CaseSettings) -> Any:
    return create_data_client(settings.supabase_url, settings.service_key.get_secret_value())


def create_app(
    *,
    combined_settings: CombinedSettings | None = None,
    banking_settings: BankingSettings | None = None,
    fraud_settings: FraudSettings | None = None,
    case_settings: CaseSettings | None = None,
    plaid: PlaidGateway | None = None,
    supabase_client: Any = None,
    force_memory: bool = False,
) -> FastAPI:
    root_settings = combined_settings or CombinedSettings()
    bank_config = banking_settings or BankingSettings()
    fraud_config = fraud_settings or FraudSettings()
    case_config = case_settings or CaseSettings()
    configure_logging(root_settings.log_level)

    banking: BankingContainer = create_banking_container(bank_config, plaid)
    local_banking = LocalBankingDataProvider(banking)
    local_case_banking = LocalCaseBankingDataProvider(local_banking)

    if force_memory:
        fraud_config = fraud_config.model_copy(update={"fraud_repository_backend": "memory", "mcp_provider_mode": "local"})
        case_config = case_config.model_copy(update={"repository_backend": "memory", "mcp_provider_mode": "local"})

    shared_supabase = supabase_client
    if not force_memory and (fraud_config.fraud_repository_backend == "supabase" or case_config.repository_backend == "supabase"):
        shared_supabase = shared_supabase or _new_supabase_client(case_config)

    fraud: FraudContainer = create_fraud_container(
        fraud_config,
        banking_provider=local_banking if root_settings.provider_mode == "local" else None,
        supabase_client=shared_supabase,
    )
    local_fraud = LocalFraudDataProvider(fraud)
    case: CaseContainer = create_case_container(
        case_config,
        memory=force_memory,
        banking=local_case_banking if root_settings.provider_mode == "local" else None,
        fraud=local_fraud if root_settings.provider_mode == "local" else None,
        supabase_client=shared_supabase,
    )

    banking_server = create_banking_mcp(banking)
    fraud_server = create_fraud_mcp(fraud)
    case_server = create_case_mcp(case)
    banking_http = banking_server.http_app(path="/")
    fraud_http = fraud_server.http_app(path="/")
    case_http = case_server.http_app(path="/")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(banking_http.lifespan(app))
            await stack.enter_async_context(fraud_http.lifespan(app))
            await stack.enter_async_context(case_http.lifespan(app))
            if root_settings.auto_migrate:
                await asyncio.to_thread(apply_all_migrations, case_config)
            if bank_config.plaid_auto_bootstrap:
                await banking.bootstrap.bootstrap()
            if case_config.case_auto_seed:
                await case.cards.upsert(CardState(card_id="card_demo_001", customer_id=bank_config.plaid_default_customer_id, updated_by="combined_startup"))
            yield

    app = FastAPI(title="ThinkFive MCP Platform", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["authorization", "content-type", "mcp-protocol-version", "mcp-session-id", "x-request-id"],
    )
    app.state.banking = banking
    app.state.fraud = fraud
    app.state.case = case
    app.state.banking_server = banking_server
    app.state.fraud_server = fraud_server
    app.state.case_server = case_server
    app.state.supabase = shared_supabase
    app.state.provider_mode = root_settings.provider_mode
    app.include_router(create_webhook_router(banking))
    app.mount("/mcp/banking", BearerTokenMiddleware(banking_http, root_settings.auth_token))
    app.mount("/mcp/fraud", BearerTokenMiddleware(fraud_http, root_settings.auth_token))
    app.mount("/mcp/case", BearerTokenMiddleware(case_http, root_settings.auth_token))

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "services": {"banking": "ok", "fraud": "ok", "case": "ok"}}

    @app.get("/ready")
    async def ready() -> JSONResponse:
        checks: dict[str, Any] = {
            "authentication": {"configured": bool(root_settings.auth_token)},
            "banking": {
                "configured": bool(bank_config.plaid_client_id.get_secret_value() and bank_config.plaid_secret.get_secret_value()),
                "repository": "memory_with_sandbox_recovery",
            },
            "fraud": {
                "provider": root_settings.provider_mode,
                "repository": fraud_config.fraud_repository_backend,
            },
            "case": {
                "provider": root_settings.provider_mode,
                "repository": case_config.repository_backend,
            },
        }
        ready_state = checks["banking"]["configured"] and checks["authentication"]["configured"]
        if not force_memory:
            ready_state = ready_state and shared_supabase is not None
            if ready_state:
                try:
                    await asyncio.to_thread(lambda: shared_supabase.table("fraud_assessments").select("assessment_id").limit(1).execute())
                    await asyncio.to_thread(lambda: shared_supabase.table("cases").select("case_id").limit(1).execute())
                    checks["supabase"] = "reachable"
                except Exception:
                    ready_state = False
                    checks["supabase"] = "unavailable_or_migrations_missing"
        else:
            checks["supabase"] = "not_required_in_test_mode"
        return JSONResponse({"status": "ready" if ready_state else "not_ready", "checks": checks}, status_code=200 if ready_state else 503)

    return app
