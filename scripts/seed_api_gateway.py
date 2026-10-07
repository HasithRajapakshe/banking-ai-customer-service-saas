import asyncio
import uuid
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Add the project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'api-gateway')))

from app.core.security import hash_password
from app.models import AppUser, Role, UserRole

from sqlalchemy import select, text

# Use the environment DATABASE_URL or default
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql+asyncpg://banking_app:change_me_in_production@localhost:5432/banking_ai"
)

async def seed():
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Fetch a valid tenant id
        tenant_result = await session.execute(text("SELECT id FROM tenant LIMIT 1"))
        tenant_row = tenant_result.fetchone()
        if not tenant_row:
            print("No tenant found. Cannot seed users.")
            return
        tenant_id = tenant_row[0]

        # Fetch valid customer ids
        customer_result = await session.execute(text(f"SELECT id FROM customer WHERE tenant_id = '{tenant_id}' LIMIT 2"))
        customers = customer_result.fetchall()
        alice_id = customers[0][0] if len(customers) > 0 else None
        bob_id = customers[1][0] if len(customers) > 1 else None

        # Create default roles
        admin_role = Role(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            role_code="ADMIN",
            role_name="Admin",
            description="Administrator"
        )
        customer_role = Role(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            role_code="CUSTOMER",
            role_name="Customer",
            description="Customer"
        )
        session.add_all([admin_role, customer_role])

        # Create user Alice
        alice = AppUser(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=alice_id,
            email="alice@example.com",
            password_hash=hash_password("password123"),
            first_name="Alice",
            last_name="Smith",
            status="active"
        )

        # Create user Bob
        bob = AppUser(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=bob_id,
            email="bob@example.com",
            password_hash=hash_password("password123"),
            first_name="Bob",
            last_name="Jones",
            status="active"
        )
        
        session.add_all([alice, bob])
        
        # Assign roles
        session.add(UserRole(user_id=alice.id, role_id=customer_role.id))
        session.add(UserRole(user_id=bob.id, role_id=customer_role.id))
        
        await session.commit()
        print("API Gateway users seeded successfully.")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())
