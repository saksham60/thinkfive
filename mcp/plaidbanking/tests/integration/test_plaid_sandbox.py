from __future__ import annotations

import os

import pytest

from plaidbanking.app.config import get_settings
from plaidbanking.app.container import create_container

pytestmark = pytest.mark.sandbox


@pytest.mark.asyncio
async def test_real_sandbox_bootstrap_accounts_and_sync() -> None:
    if os.getenv("RUN_PLAID_SANDBOX_TESTS", "false").casefold() != "true":
        pytest.skip("Set RUN_PLAID_SANDBOX_TESTS=true to run real Plaid Sandbox tests.")
    settings = get_settings()
    assert settings.plaid_env == "sandbox"
    container = create_container(settings)
    await container.bootstrap.bootstrap()
    customer = settings.plaid_default_customer_id
    accounts = await container.banking.get_accounts(customer, balance=True)
    summary = await container.transaction_service.sync(customer)
    assert accounts and summary.sync_completed
