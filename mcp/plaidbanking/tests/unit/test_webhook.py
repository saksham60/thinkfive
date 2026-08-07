from __future__ import annotations

import hashlib
import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from plaidbanking.app.plaid.exceptions import WebhookVerificationError
from plaidbanking.app.webhook.handlers import handle_webhook
from plaidbanking.app.webhook.verification import PlaidWebhookVerifier
from plaidbanking.tests.conftest import FakePlaid


def signed(fake_plaid: FakePlaid, body: bytes, *, issued_at: float | None = None, body_hash: str | None = None) -> str:
    private = ec.generate_private_key(ec.SECP256R1())
    public_jwk = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(private.public_key()))
    public_jwk.update({"kid": "key-1", "alg": "ES256", "use": "sig"})
    fake_plaid.webhook_jwk = public_jwk
    claims = {"iat": issued_at or time.time(), "request_body_sha256": body_hash or hashlib.sha256(body).hexdigest()}
    return jwt.encode(claims, private, algorithm="ES256", headers={"kid": "key-1", "alg": "ES256"})


@pytest.mark.asyncio
async def test_valid_webhook_marks_customer_stale(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer", "token", "item-1")
    body = b'{"webhook_type":"TRANSACTIONS","webhook_code":"SYNC_UPDATES_AVAILABLE","item_id":"item-1"}'
    await PlaidWebhookVerifier(fake_plaid).verify(body, signed(fake_plaid, body))
    response, status = await handle_webhook(container, body)
    assert status == 200 and response["handled"] is True
    assert (await container.sync_states.get("customer")).stale


@pytest.mark.asyncio
async def test_duplicate_webhook_is_idempotent(container) -> None:
    await container.items.register_item("customer", "token", "item-1")
    body = b'{"webhook_type":"TRANSACTIONS","webhook_code":"SYNC_UPDATES_AVAILABLE","item_id":"item-1"}'
    await handle_webhook(container, body)
    response, status = await handle_webhook(container, body)
    assert status == 200 and response["duplicate"] is True


@pytest.mark.asyncio
async def test_unknown_item_and_malformed_body(container) -> None:
    response, status = await handle_webhook(container, b'{"webhook_type":"TRANSACTIONS","webhook_code":"SYNC_UPDATES_AVAILABLE","item_id":"missing"}')
    assert status == 202 and response["reason"] == "unknown_item"
    _, malformed_status = await handle_webhook(container, b"not-json")
    assert malformed_status == 400


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["missing", "expired", "bad_hash", "wrong_alg"])
async def test_invalid_webhook_verification(fake_plaid: FakePlaid, case: str) -> None:
    body = b"{}"
    verifier = PlaidWebhookVerifier(fake_plaid)
    if case == "missing":
        token = None
    elif case == "expired":
        token = signed(fake_plaid, body, issued_at=time.time() - 301)
    elif case == "bad_hash":
        token = signed(fake_plaid, body, body_hash="0" * 64)
    else:
        token = jwt.encode(
            {"iat": time.time(), "request_body_sha256": hashlib.sha256(body).hexdigest()},
            "secret",
            algorithm="HS256",
            headers={"kid": "key-1"},
        )
    with pytest.raises(WebhookVerificationError):
        await verifier.verify(body, token)
