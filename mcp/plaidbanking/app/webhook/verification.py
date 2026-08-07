from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any

import jwt

from plaidbanking.app.plaid.client import PlaidGateway
from plaidbanking.app.plaid.exceptions import WebhookVerificationError


@dataclass(slots=True)
class CachedKey:
    key: Any
    expires_at: float


class PlaidWebhookVerifier:
    def __init__(self, plaid: PlaidGateway, replay_seconds: int = 300, cache_seconds: int = 3600) -> None:
        self.plaid = plaid
        self.replay_seconds = replay_seconds
        self.cache_seconds = cache_seconds
        self._keys: dict[str, CachedKey] = {}

    async def verify(self, raw_body: bytes, token: str | None) -> dict[str, Any]:
        if not token:
            raise WebhookVerificationError("Missing Plaid-Verification header.")
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            raise WebhookVerificationError("Malformed Plaid verification token.") from None
        if header.get("alg") != "ES256" or not isinstance(header.get("kid"), str):
            raise WebhookVerificationError("Unsupported Plaid webhook signing metadata.")
        key = await self._get_key(header["kid"])
        try:
            claims: dict[str, Any] = jwt.decode(token, key=key, algorithms=["ES256"], options={"require": ["iat", "request_body_sha256"]}, leeway=5)
        except jwt.PyJWTError:
            raise WebhookVerificationError("Invalid Plaid webhook signature.") from None
        issued_at = claims.get("iat")
        now = time.time()
        if not isinstance(issued_at, (int, float)) or issued_at > now + 5 or now - issued_at > self.replay_seconds:
            raise WebhookVerificationError("Expired Plaid webhook verification token.")
        actual_hash = hashlib.sha256(raw_body).hexdigest()
        if not hmac.compare_digest(actual_hash, str(claims.get("request_body_sha256", ""))):
            raise WebhookVerificationError("Plaid webhook body hash did not match.")
        return claims

    async def _get_key(self, key_id: str) -> Any:
        cached = self._keys.get(key_id)
        now = time.monotonic()
        if cached and cached.expires_at > now:
            return cached.key
        response = await self.plaid.webhook_key(key_id)
        jwk = response.get("key")
        if not isinstance(jwk, dict) or jwk.get("alg") != "ES256" or jwk.get("kid") != key_id:
            raise WebhookVerificationError("Plaid returned an invalid webhook verification key.")
        key = jwt.PyJWK.from_dict(jwk).key
        self._keys[key_id] = CachedKey(key, now + self.cache_seconds)
        return key
