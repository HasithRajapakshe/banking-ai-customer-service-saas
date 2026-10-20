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
        tenant_id: uuid.UUID,
    ):
        return await self.repository.get_by_customer_id(
            db=db,
            customer_id=customer_id,
            tenant_id=tenant_id,
        )

    async def get_account(
        self,
        db: AsyncSession,
        account_id: uuid.UUID,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ):
        return await self.repository.get_by_id(
            db=db,
            account_id=account_id,
            customer_id=customer_id,
            tenant_id=tenant_id,
        )

    async def get_balance(
        self,
        db: AsyncSession,
        account_id: uuid.UUID,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ):
        return await self.repository.get_by_id(
            db=db,
            account_id=account_id,
            customer_id=customer_id,
            tenant_id=tenant_id,
        )