from __future__ import annotations

from typing import Any

from .common import StrictModel


class IdentityAccount(StrictModel):
    account_id: str
    owners: tuple[dict[str, Any], ...] = ()


class CustomerIdentity(StrictModel):
    accounts: tuple[IdentityAccount, ...] = ()
    capability_available: bool = True


class IdentityVerification(StrictModel):
    capability_available: bool
    match: dict[str, Any] | None = None
    reason: str | None = None
