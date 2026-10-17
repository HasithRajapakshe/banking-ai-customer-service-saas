"""Seed API Gateway reference data (roles, permissions) and demo users.

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

# (role_code, role_name, description); tenant_id NULL = global role.
ROLES = [
    ("CUSTOMER", "Customer", "Standard banking customer"),
    ("SUPPORT_AGENT", "Support Agent", "Human customer support agent"),
    ("ADMIN", "Administrator", "Tenant administrator"),
]

# (permission_code, permission_name, description)
PERMISSIONS = [
    ("chat.read", "Read conversations", "Read customer conversations"),
    ("chat.write", "Send messages", "Send customer service messages"),
    ("account.read", "Read account information", "View authorized account information"),
    ("transaction.read", "Read transactions", "View authorized account transactions"),
    ("card.read", "Read card information", "View authorized card information"),
    ("card.block", "Block card", "Block an authorized customer card"),
    ("loan.read", "Read loan information", "View authorized loan information"),
    ("payment.read", "Read payments", "View payment information"),
    ("payment.create", "Create payment", "Create an authorized payment"),
    ("complaint.create", "Create complaint", "Create a customer complaint"),
    ("complaint.read", "Read complaint", "Read complaint information"),
    ("ticket.create", "Create support ticket", "Create customer support ticket"),
    ("ticket.read", "Read support ticket", "Read support ticket"),
    ("knowledge.read", "Read knowledge base", "Retrieve approved knowledge"),
    ("knowledge.write", "Manage knowledge base", "Create and update knowledge"),
    ("knowledge.publish", "Publish knowledge", "Approve and publish knowledge"),
    ("analytics.read", "Read analytics", "View tenant analytics"),
    ("admin.users", "Manage users", "Manage tenant users"),
    ("admin.roles", "Manage roles", "Manage roles and permissions"),
    ("audit.read", "Read audit logs", "View security and activity audit logs"),
    # Checked by api-gateway admin routes.
    ("knowledge.manage", "Manage knowledge documents", "Upload and list knowledge documents"),
    ("users.manage", "Manage users (admin API)", "List and manage tenant users"),
]

ROLE_PERMISSIONS = {
    "ADMIN": ["knowledge.manage", "audit.read", "users.manage"],
}

# (email, first_name, last_name, role_code, customer_slot); slot None = no customer.
DEMO_USERS = [
    ("admin@example.com", "Admin", "User", "ADMIN", None),
    ("alice@example.com", "Alice", "Smith", "CUSTOMER", 0),
    ("bob@example.com", "Bob", "Jones", "CUSTOMER", 1),
]


async def seed_reference_data(conn: AsyncConnection) -> None:
    for role_code, role_name, description in ROLES:
        await conn.execute(
            text(
                """
                INSERT INTO role (tenant_id, role_code, role_name, description)
                VALUES (NULL, :role_code, :role_name, :description)
                ON CONFLICT (role_code) WHERE tenant_id IS NULL DO NOTHING
                """
            ),
            {"role_code": role_code, "role_name": role_name, "description": description},
        )

    for code, name, description in PERMISSIONS:
        await conn.execute(
            text(
                """
                INSERT INTO permission (permission_code, permission_name, description)
                VALUES (:code, :name, :description)
                ON CONFLICT (permission_code) DO NOTHING
                """
            ),
            {"code": code, "name": name, "description": description},
        )

    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        for permission_code in permission_codes:
            await conn.execute(
                text(
                    """
                    INSERT INTO role_permission (role_id, permission_id)
                    SELECT r.id, p.id
                    FROM role r, permission p
                    WHERE r.tenant_id IS NULL
                      AND r.role_code = :role_code
                      AND p.permission_code = :permission_code
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"role_code": role_code, "permission_code": permission_code},
            )
    print(f"Reference data: {len(ROLES)} roles, {len(PERMISSIONS)} permissions.")


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
            await seed_reference_data(conn)
            await seed_demo_users(conn)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
