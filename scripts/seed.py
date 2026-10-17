"""Run all seeds in dependency order. Every step is idempotent.

1. Roles and permissions (the bank dataset assigns users to CUSTOMER / SUPPORT_AGENT).
2. Synthetic bank dataset (tenant, customers, accounts, cards, ...).
3. Demo users (alice, bob, admin), linked to customers from step 2.
"""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from seed_api_gateway import DATABASE_URL, seed_demo_users, seed_reference_data
from seed_bank_data import seed_bank_data


async def main() -> None:
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as conn:
            await seed_reference_data(conn)
        await seed_bank_data(engine)
        async with engine.begin() as conn:
            await seed_demo_users(conn)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
