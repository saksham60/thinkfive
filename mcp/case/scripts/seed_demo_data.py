from __future__ import annotations

import asyncio

from case.app.config import Settings
from case.app.container import create_container
from case.app.models.domain import CardState


async def main() -> None:
    c = create_container(Settings())
    await c.cards.upsert(CardState(card_id="card_demo_001", customer_id="demo_customer_001", updated_by="seed_demo_data"))
    print("Seeded card_demo_001 as synthetic demo bank state.")


if __name__ == "__main__":
    asyncio.run(main())
