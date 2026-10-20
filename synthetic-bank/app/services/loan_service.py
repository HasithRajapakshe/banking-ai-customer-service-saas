import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.loan_repository import LoanRepository
from app.repositories.loan_payment_repository import (
    LoanPaymentRepository,
)


class LoanService:

    def __init__(self):
        self.loan_repository = LoanRepository()
        self.payment_repository = LoanPaymentRepository()

    async def get_loan(
        self,
        db: AsyncSession,
        loan_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ):
        return await self.loan_repository.get_by_id(
            db,
            loan_id,
            tenant_id,
            customer_id,
        )

    async def get_customer_loans(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self.loan_repository.get_by_customer_id(
            db,
            customer_id,
            tenant_id,
            limit,
            offset,
        )

    async def get_loan_payments(
        self,
        db: AsyncSession,
        loan_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self.payment_repository.get_by_loan_id(
            db,
            loan_id,
            tenant_id,
            limit,
            offset,
        )