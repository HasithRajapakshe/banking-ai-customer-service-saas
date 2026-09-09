import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository:

    async def get_by_customer_id(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[Account]:

        result = await db.execute(
            select(Account)
            .where(
                Account.customer_id == customer_id,
                Account.tenant_id == tenant_id,
            )
            .order_by(
                Account.account_type,
                Account.account_number,
            )
        )

        return list(result.scalars().all())

    async def get_by_id(
        self,
        db: AsyncSession,
        account_id: uuid.UUID,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> Account | None:

        result = await db.execute(
            select(Account)
            .where(
                Account.id == account_id,
                Account.customer_id == customer_id,
                Account.tenant_id == tenant_id,
            )
        )

        return result.scalar_one_or_none()