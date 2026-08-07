from __future__ import annotations

import asyncio

from plaidbanking.app.config import get_settings
from plaidbanking.app.container import create_container


async def main() -> None:
    settings = get_settings()
    if settings.plaid_env != "sandbox":
        raise SystemExit("Sandbox bootstrap is disabled outside PLAID_ENV=sandbox.")
    container = create_container(settings)
    created = await container.bootstrap.bootstrap()
    status = "created" if created else "already registered"
    print(f"Sandbox customer {settings.plaid_default_customer_id}: {status}")
    print("No Plaid tokens were printed.")


if __name__ == "__main__":
    asyncio.run(main())
