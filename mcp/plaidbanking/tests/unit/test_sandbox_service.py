from __future__ import annotations

import pytest

from plaidbanking.app.config import Settings
from plaidbanking.app.container import create_container
from plaidbanking.app.plaid.exceptions import InvalidInputError
from plaidbanking.tests.conftest import FakePlaid


@pytest.mark.asyncio
async def test_sandbox_transaction_marks_stale(container, fake_plaid: FakePlaid) -> None:
    await container.items.register_item("customer", "token", "item")
    result = await container.sandbox.simulate_transaction("customer", 25, "Synthetic purchase")
    assert result["synthetic"] is True
    assert (await container.sync_states.get("customer")).stale
    assert fake_plaid.created_transactions[0][1:3] == (25, "Synthetic purchase")


@pytest.mark.asyncio
async def test_sandbox_mutation_denied_in_production(fake_plaid: FakePlaid) -> None:
    settings = Settings(_env_file=None, PLAID_CLIENT_ID="client", PLAID_SECRET="secret", PLAID_ENV="production", PLAID_AUTO_BOOTSTRAP=False)
    container = create_container(settings, fake_plaid)
    await container.items.register_item("customer", "token", "item")
    with pytest.raises(InvalidInputError):
        await container.sandbox.simulate_transaction("customer", 25, "Denied")


@pytest.mark.asyncio
async def test_bootstrap_is_idempotent(settings: Settings, fake_plaid: FakePlaid) -> None:
    configured = settings.model_copy(update={"plaid_auto_bootstrap": True})
    container = create_container(configured, fake_plaid)
    assert await container.bootstrap.bootstrap() is True
    assert await container.bootstrap.bootstrap() is False
    assert await container.items.exists("demo_customer_001")
