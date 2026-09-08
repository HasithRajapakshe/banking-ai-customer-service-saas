import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer


class CustomerRepository:

    async def get_by_id(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
    ) -> Customer | None:

        result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )

        return result.scalar_one_or_none()
