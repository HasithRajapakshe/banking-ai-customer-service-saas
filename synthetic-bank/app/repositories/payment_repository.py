import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


class PaymentRepository:

    async def get_by_id(
        self,
        db: AsyncSession,
        payment_id: uuid.UUID,
    ) -> Payment | None:

        result = await db.execute(
            select(Payment)
            .where(Payment.id == payment_id)
        )

        return result.scalar_one_or_none()

    async def get_by_customer_id(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Payment]:

        result = await db.execute(
            select(Payment)
            .where(
                Payment.customer_id == customer_id
            )
            .order_by(
                Payment.created_at.desc(),
                Payment.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())

    async def get_by_idempotency_key(
        self,
        db: AsyncSession,
        idempotency_key: str,
    ) -> Payment | None:

        result = await db.execute(
            select(Payment)
            .where(
                Payment.idempotency_key == idempotency_key
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        payment: Payment,
    ) -> Payment:

        db.add(payment)

        await db.commit()
        await db.refresh(payment)

        return payment

    async def cancel(
        self,
        db: AsyncSession,
        payment: Payment,
    ) -> Payment:

        payment.status = "cancelled"
        payment.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(payment)

        return payment