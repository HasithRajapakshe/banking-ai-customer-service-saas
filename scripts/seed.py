"""Run all seeds in dependency order. Every step is idempotent.

Runs after `alembic upgrade head`, which already created the global roles and
permissions (revision 0002); the bank dataset assigns users to those roles.

1. Synthetic bank dataset (tenant, customers, accounts, cards, ...).
2. Demo users (alice, bob, admin), linked to customers from step 1.
"""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from seed_api_gateway import DATABASE_URL, seed_demo_users
from seed_bank_data import seed_bank_data


async def main() -> None:
    engine = create_async_engine(DATABASE_URL)
    try:
        await seed_bank_data(engine)
        async with engine.begin() as conn:
            await seed_demo_users(conn)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
