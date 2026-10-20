import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan_payment import LoanPayment


class LoanPaymentRepository:

    async def get_by_loan_id(
        self,
        db: AsyncSession,
        loan_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[LoanPayment]:

        result = await db.execute(
            select(LoanPayment)
            .where(
                LoanPayment.loan_id == loan_id,
                LoanPayment.tenant_id == tenant_id,
            )
            .order_by(
                LoanPayment.installment_number.asc(),
                LoanPayment.id.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())