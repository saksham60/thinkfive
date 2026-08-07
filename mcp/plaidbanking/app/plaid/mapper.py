from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from plaidbanking.app.models.account import Account
from plaidbanking.app.models.identity import CustomerIdentity, IdentityAccount, IdentityVerification
from plaidbanking.app.models.liability import Liabilities
from plaidbanking.app.models.transaction import Transaction


def plain(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, (date, datetime, Decimal, str, int, float, bool)) or value is None:
        return value
    return str(value)


def _enum(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def map_account(value: dict[str, Any]) -> Account:
    balances = value.get("balances") or {}
    return Account(
        account_id=value["account_id"],
        name=value.get("name") or "Unavailable",
        official_name=value.get("official_name"),
        type=_enum(value.get("type")) or "unknown",
        subtype=_enum(value.get("subtype")),
        mask=value.get("mask"),
        available_balance=balances.get("available"),
        current_balance=balances.get("current"),
        currency=balances.get("iso_currency_code") or balances.get("unofficial_currency_code"),
    )


def map_transaction(customer_id: str, value: dict[str, Any]) -> Transaction:
    category = value.get("category") or []
    return Transaction(
        customer_id=customer_id,
        transaction_id=value["transaction_id"],
        account_id=value["account_id"],
        amount=value.get("amount", 0),
        currency=value.get("iso_currency_code") or value.get("unofficial_currency_code"),
        merchant_name=value.get("merchant_name"),
        transaction_name=value.get("name") or "Unavailable",
        date=value["date"],
        authorized_date=value.get("authorized_date"),
        datetime=value.get("datetime"),
        pending=bool(value.get("pending", False)),
        category=tuple(category),
        personal_finance_category=plain(value.get("personal_finance_category")),
        payment_channel=_enum(value.get("payment_channel")),
        location=plain(value.get("location")),
        website=value.get("website"),
        logo_url=value.get("logo_url"),
        entity_id=value.get("entity_id"),
    )


def map_identity(payload: dict[str, Any]) -> CustomerIdentity:
    accounts = []
    for account in payload.get("accounts", []):
        accounts.append(IdentityAccount(account_id=account["account_id"], owners=tuple(plain(account.get("owners") or []))))
    return CustomerIdentity(accounts=tuple(accounts))


def map_identity_match(payload: dict[str, Any]) -> IdentityVerification:
    return IdentityVerification(capability_available=True, match=plain(payload))


def map_liabilities(payload: dict[str, Any]) -> Liabilities:
    liabilities = payload.get("liabilities") or {}
    return Liabilities(
        capability_available=True,
        credit=tuple(plain(liabilities.get("credit") or [])),
        mortgages=tuple(plain(liabilities.get("mortgage") or [])),
        student_loans=tuple(plain(liabilities.get("student") or [])),
    )
