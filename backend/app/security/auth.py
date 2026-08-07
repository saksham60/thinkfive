"""Authentication - demo cookie-session mode with AuthProvider abstraction."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Protocol
from uuid import UUID

from app.core.config import Settings
from app.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class AuthProvider(Protocol):
    """Abstraction so demo auth can be swapped for Supabase Auth later."""

    async def authenticate(self, email: str, password: str) -> AuthenticatedUser:
        ...

    def create_session_token(self, user: AuthenticatedUser) -> str:
        ...

    def verify_session_token(self, token: str) -> AuthenticatedUser:
        ...


class AuthenticatedUser:
    """Authenticated user identity."""

    def __init__(self, user_id: UUID, email: str, role: str, customer_id: str | None) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role
        self.customer_id = customer_id

    def to_dict(self) -> dict[str, str | None]:
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "role": self.role,
            "customer_id": self.customer_id,
        }


class DemoAuthProvider:
    """Demo authentication provider - signs a session token with HMAC.

    Issues an HttpOnly cookie session. Passwords are checked via the
    app_users table (hashed with passlib in a full implementation); for the
    hackathon demo, any registered email in app_users is accepted so long
    as the record exists and is active, matching AUTH_MODE=demo.
    """

    def __init__(self, settings: Settings, user_repo: object) -> None:
        self.settings = settings
        self.user_repo = user_repo
        self._secret = settings.session_secret.encode()

    def create_session_token(self, user: AuthenticatedUser) -> str:
        payload = json.dumps(user.to_dict(), separators=(",", ":"))
        payload_b64 = payload.encode().hex()
        signature = hmac.new(self._secret, payload_b64.encode(), hashlib.sha256).hexdigest()
        return f"{payload_b64}.{signature}"

    def verify_session_token(self, token: str) -> AuthenticatedUser:
        try:
            payload_b64, signature = token.split(".", 1)
        except ValueError:
            raise AuthenticationError("Malformed session token")

        expected_signature = hmac.new(self._secret, payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise AuthenticationError("Invalid session signature")

        data = json.loads(bytes.fromhex(payload_b64).decode())
        return AuthenticatedUser(
            user_id=UUID(data["user_id"]),
            email=data["email"],
            role=data["role"],
            customer_id=data.get("customer_id"),
        )
