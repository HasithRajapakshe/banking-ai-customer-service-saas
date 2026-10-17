"""Load the synthetic bank dataset (database/seeds/002_seed_synthetic_data.sql).

Runs only when the configured tenant does not exist yet, so it is safe to call
on every `docker compose up`. The SQL file manages its own transaction.
"""

import asyncio
import os
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://banking_app:change_me_in_production@localhost:5432/banking_ai",
)
TENANT_ID = uuid.UUID(os.environ.get("TENANT_ID", "f498100f-80c4-467e-84ec-ebfe5470b442"))
SEED_SQL_PATH = Path(
    os.environ.get(
        "SEED_SQL_PATH",
        Path(__file__).resolve().parent.parent / "database" / "seeds" / "002_seed_synthetic_data.sql",
    )
)


async def seed_bank_data(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT EXISTS (SELECT 1 FROM tenant WHERE id = :tenant_id)"),
            {"tenant_id": TENANT_ID},
        )
    if exists:
        print(f"Synthetic bank data already present for tenant {TENANT_ID}; skipping.")
        return

    script = SEED_SQL_PATH.read_text(encoding="utf-8")
    async with engine.connect() as conn:
        raw = await conn.get_raw_connection()
        # asyncpg's execute() without arguments uses the simple query protocol,
        # which runs a multi-statement script (including its BEGIN/COMMIT).
        await raw.driver_connection.execute(script)
    print(f"Loaded synthetic bank data from {SEED_SQL_PATH.name}.")


async def main() -> None:
    engine = create_async_engine(DATABASE_URL)
    try:
        await seed_bank_data(engine)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
