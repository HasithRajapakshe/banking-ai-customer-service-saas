import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.account_repository import AccountRepository


class AccountService:

    def __init__(self):
        self.repository = AccountRepository()

    async def get_accounts_by_customer(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
    ):
        return await self.repository.get_by_customer_id(
            db,
            customer_id,
        )

    async def get_account(
        self,
        db: AsyncSession,
        account_id: uuid.UUID,
    ):
        return await self.repository.get_by_id(
            db,
            account_id,
        )

    async def get_account_balance(
        self,
        db: AsyncSession,
        account_id: uuid.UUID,
    ):
        return await self.repository.get_by_id(
            db,
            account_id,
        )