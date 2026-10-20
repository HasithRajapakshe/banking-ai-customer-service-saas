import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_transaction import AccountTransaction


class AccountTransactionRepository:

    async def get_by_account_id(
        self,
        db: AsyncSession,
        account_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AccountTransaction]:

        result = await db.execute(
            select(AccountTransaction)
            .where(
                AccountTransaction.account_id == account_id,
                AccountTransaction.tenant_id == tenant_id,
            )
            .order_by(
                AccountTransaction.transaction_at.desc(),
                AccountTransaction.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())