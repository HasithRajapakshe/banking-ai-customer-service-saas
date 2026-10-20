"""Seed the demo users (roles and permissions come from Alembic revision 0002).

Idempotent: safe to run on every `docker compose up`. All SQL uses bound
parameters.

Demo logins (password for all: password123):
  admin@example.com  ADMIN     (no customer link)
  alice@example.com  CUSTOMER  (first active customer with an active card)
  bob@example.com    CUSTOMER  (second active customer with an active card)
"""

import asyncio
import os
import uuid

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://banking_app:change_me_in_production@localhost:5432/banking_ai",
)
TENANT_ID = uuid.UUID(os.environ.get("TENANT_ID", "f498100f-80c4-467e-84ec-ebfe5470b442"))
DEMO_PASSWORD = "password123"


# (email, first_name, last_name, role_code, customer_slot); slot None = no customer.
DEMO_USERS = [
    ("admin@example.com", "Admin", "User", "ADMIN", None),
    ("alice@example.com", "Alice", "Smith", "CUSTOMER", 0),
    ("bob@example.com", "Bob", "Jones", "CUSTOMER", 1),
]



async def _demo_customer_ids(conn: AsyncConnection) -> list[uuid.UUID]:
    """Active customers that own an active account and an active card, in a stable order."""
    result = await conn.execute(
        text(
            """
            SELECT c.id
            FROM customer c
            WHERE c.tenant_id = :tenant_id
              AND c.status = 'active'
              AND EXISTS (SELECT 1 FROM account a
                          WHERE a.customer_id = c.id AND a.status = 'active')
              AND EXISTS (SELECT 1 FROM card k
                          WHERE k.customer_id = c.id AND k.status = 'active')
            ORDER BY c.customer_number
            LIMIT 2
            """
        ),
        {"tenant_id": TENANT_ID},
    )
    return [row[0] for row in result.fetchall()]


async def seed_demo_users(conn: AsyncConnection) -> None:
    customer_ids = await _demo_customer_ids(conn)
    if len(customer_ids) < 2:
        raise RuntimeError(
            "Need at least two active customers with an active account and card; "
            f"found {len(customer_ids)}. Has the synthetic bank data been loaded?"
        )

    password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()

    for email, first_name, last_name, role_code, slot in DEMO_USERS:
        customer_id = customer_ids[slot] if slot is not None else None
        result = await conn.execute(
            text(
                """
                INSERT INTO app_user
                    (tenant_id, customer_id, email, password_hash, first_name, last_name, status)
                VALUES
                    (:tenant_id, :customer_id, :email, :password_hash, :first_name, :last_name, 'active')
                ON CONFLICT (tenant_id, email) DO UPDATE SET
                    customer_id = EXCLUDED.customer_id,
                    password_hash = EXCLUDED.password_hash,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    status = 'active'
                RETURNING id
                """
            ),
            {
                "tenant_id": TENANT_ID,
                "customer_id": customer_id,
                "email": email,
                "password_hash": password_hash,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        user_id = result.scalar_one()

        await conn.execute(
            text(
                """
                INSERT INTO user_role (user_id, role_id)
                SELECT :user_id, r.id
                FROM role r
                WHERE r.tenant_id IS NULL AND r.role_code = :role_code
                ON CONFLICT DO NOTHING
                """
            ),
            {"user_id": user_id, "role_code": role_code},
        )
        print(f"Demo user {email} ({role_code}) customer_id={customer_id}")


async def main() -> None:
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as conn:
            await seed_demo_users(conn)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
