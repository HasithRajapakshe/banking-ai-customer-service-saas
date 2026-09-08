import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan


class LoanRepository:

    async def get_by_id(
        self,
        db: AsyncSession,
        loan_id: uuid.UUID,
    ) -> Loan | None:

        result = await db.execute(
            select(Loan)
            .where(Loan.id == loan_id)
        )

        return result.scalar_one_or_none()

    async def get_by_customer_id(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Loan]:

        result = await db.execute(
            select(Loan)
            .where(
                Loan.customer_id == customer_id
            )
            .order_by(
                Loan.created_at.desc(),
                Loan.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())