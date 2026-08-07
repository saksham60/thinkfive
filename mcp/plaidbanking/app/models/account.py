from __future__ import annotations

from collections import Counter
from decimal import Decimal

from pydantic import Field

from .common import StrictModel


class Account(StrictModel):
    account_id: str
    name: str
    official_name: str | None = None
    type: str
    subtype: str | None = None
    mask: str | None = None
    available_balance: Decimal | None = None
    current_balance: Decimal | None = None
    currency: str | None = None


class AccountBalance(StrictModel):
    account_id: str
    account_name: str
    current_balance: Decimal | None = None
    available_balance: Decimal | None = None
    currency: str | None = None


class CurrencyTotals(StrictModel):
    currency: str
    current_balance: Decimal = Decimal("0")
    available_balance: Decimal = Decimal("0")


class AccountSummary(StrictModel):
    account_count: int = Field(ge=0)
    account_types: dict[str, int]
    accounts: tuple[Account, ...]
    totals_by_currency: tuple[CurrencyTotals, ...]

    @classmethod
    def from_accounts(cls, accounts: list[Account]) -> AccountSummary:
        totals: dict[str, list[Decimal]] = {}
        for account in accounts:
            currency = account.currency or "unavailable"
            values = totals.setdefault(currency, [Decimal("0"), Decimal("0")])
            values[0] += account.current_balance or Decimal("0")
            values[1] += account.available_balance or Decimal("0")
        return cls(
            account_count=len(accounts),
            account_types=dict(Counter(account.type for account in accounts)),
            accounts=tuple(accounts),
            totals_by_currency=tuple(
                CurrencyTotals(currency=currency, current_balance=values[0], available_balance=values[1]) for currency, values in sorted(totals.items())
            ),
        )
