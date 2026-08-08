from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from plaidbanking.app.container import Container
from plaidbanking.app.plaid.exceptions import WebhookVerificationError

from .handlers import handle_webhook
from .verification import PlaidWebhookVerifier


def create_webhook_router(container: Container) -> APIRouter:
    router = APIRouter()
    verifier = PlaidWebhookVerifier(container.plaid, container.settings.webhook_replay_seconds) if container.plaid is not None else None

    @router.post("/webhooks/plaid")
    async def plaid_webhook(request: Request) -> JSONResponse:
        if verifier is None:
            return JSONResponse(
                {"accepted": True, "handled": False, "reason": "supabase_is_canonical_provider"},
                status_code=202,
            )
        raw_body = await request.body()
        try:
            await verifier.verify(raw_body, request.headers.get("Plaid-Verification"))
        except WebhookVerificationError as exc:
            return JSONResponse({"accepted": False, "error": exc.safe_message}, status_code=401)
        response, status = await handle_webhook(container, raw_body)
        return JSONResponse(response, status_code=status)

    return router
