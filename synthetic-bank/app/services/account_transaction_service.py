import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.account_transaction_repository import (
    AccountTransactionRepository,
)


class AccountTransactionService:

    def __init__(self):
        self.repository = AccountTransactionRepository()

    async def get_account_transactions(
        self,
        db: AsyncSession,
        account_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self.repository.get_by_account_id(
            db,
            account_id,
            tenant_id,
            limit,
            offset,
        )