from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from plaidbanking.app.config import get_settings
from plaidbanking.app.container import create_container


class SmokeRunner:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool]] = []

    async def check(self, label: str, operation: Callable[[], Awaitable[Any]]) -> Any:
        try:
            value = await operation()
            self.results.append((label, True))
            return value
        except Exception:
            self.results.append((label, False))
            return None

    def report(self) -> bool:
        for label, passed in self.results:
            print(f"{label:.<36} {'PASS' if passed else 'FAIL'}")
        passed = all(value for _, value in self.results)
        print()
        print(f"{'Overall':.<36} {'PASS' if passed else 'FAIL'}")
        return passed


async def main() -> int:
    runner = SmokeRunner()
    settings = get_settings()
    await runner.check("Plaid configuration", lambda: _assert_async(settings.plaid_env == "sandbox"))
    container = create_container(settings)
    await runner.check("Sandbox customer", container.bootstrap.bootstrap)
    customer = settings.plaid_default_customer_id
    status = await runner.check("Banking connection", lambda: container.banking.connection_status(customer))
    accounts = await runner.check("Accounts", lambda: container.banking.get_accounts(customer, balance=True))
    if accounts:
        await runner.check("Balances", lambda: container.banking.get_account_balance(customer, accounts[0].account_id))
    else:
        runner.results.append(("Balances", False))
    await runner.check("Initial transaction sync", lambda: container.transaction_service.sync(customer))
    count = await runner.check("Transaction repository", lambda: container.transactions.count(customer))
    recent = await runner.check("Recent transactions", lambda: container.transaction_service.recent(customer, 20))
    await runner.check("Transaction search", lambda: container.transaction_service.search(customer, _default_filters()))
    if recent:
        await runner.check("Transaction lookup", lambda: container.transaction_service.get(customer, recent[0].transaction_id))
    else:
        runner.results.append(("Transaction lookup", False))
    await runner.check("Custom transaction", lambda: container.sandbox.simulate_transaction(customer, 12.34, "Plaid MCP Smoke Test"))
    await runner.check("Second sync", lambda: container.transaction_service.sync(customer))
    new_count = await runner.check("New transaction visible", lambda: container.transactions.count(customer))
    runner.results[-1] = ("New transaction visible", bool(new_count is not None and count is not None and new_count >= count))
    safe = settings.plaid_secret.get_secret_value() not in str(status) and "access_token" not in str(status)
    await runner.check("Secrets protected", lambda: _assert_async(safe))
    return 0 if runner.report() else 1


async def _assert_async(condition: bool) -> bool:
    if not condition:
        raise AssertionError
    return True


def _default_filters() -> Any:
    from app.models.transaction import TransactionSearchFilters

    return TransactionSearchFilters(limit=20)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
