from __future__ import annotations

from decimal import Decimal

import pytest

from plaidbanking.app.plaid.exceptions import CustomerNotFoundError, ResourceNotFoundError
from plaidbanking.tests.conftest import FakePlaid


@pytest.mark.asyncio
async def test_accounts_balances_and_multi_currency_summary(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer", "token", "item")
    fake_plaid.accounts_payload = {
        "accounts": [
            {
                "account_id": "usd",
                "name": "Checking",
                "type": "depository",
                "subtype": "checking",
                "balances": {"current": 100, "available": 90, "iso_currency_code": "USD"},
            },
            {
                "account_id": "eur",
                "name": "Europe",
                "type": "depository",
                "balances": {"current": 50, "available": 40, "iso_currency_code": "EUR"},
            },
        ]
    }
    accounts = await container.banking.get_accounts("customer", balance=True)
    balance = await container.banking.get_account_balance("customer", "usd")
    summary = await container.banking.get_account_summary("customer")
    assert len(accounts) == 2 and balance.current_balance == Decimal("100")
    assert {value.currency for value in summary.totals_by_currency} == {"USD", "EUR"}


@pytest.mark.asyncio
async def test_unknown_customer_and_cross_customer_account_denied(container, fake_plaid: FakePlaid) -> None:
    with pytest.raises(CustomerNotFoundError):
        await container.banking.get_accounts("unknown")
    await container.items.register_item("customer", "token", "item")
    fake_plaid.accounts_payload = {"accounts": [{"account_id": "owned", "name": "Owned", "type": "depository", "balances": {}}]}
    with pytest.raises(ResourceNotFoundError):
        await container.banking.get_account_balance("customer", "other-customer-account")


@pytest.mark.asyncio
async def test_identity_and_liabilities(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer", "token", "item")
    fake_plaid.identity_payload = {"accounts": [{"account_id": "a1", "owners": [{"names": ["Test User"], "emails": []}]}]}
    fake_plaid.liabilities_payload = {"liabilities": {"credit": [{"account_id": "a1", "minimum_payment_amount": 25}], "mortgage": [], "student": []}}
    identity = await container.banking.get_identity("customer")
    verification = await container.banking.verify_identity("customer", name="Test User", phone=None, email=None, address=None)
    liabilities = await container.banking.get_liabilities("customer")
    assert identity.accounts[0].owners[0]["names"] == ["Test User"]
    assert verification.capability_available and liabilities.credit[0]["minimum_payment_amount"] == 25
