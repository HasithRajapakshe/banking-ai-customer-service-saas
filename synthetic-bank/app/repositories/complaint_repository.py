import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint


class ComplaintRepository:

    async def get_by_id(
        self,
        db: AsyncSession,
        complaint_id: uuid.UUID,
    ) -> Complaint | None:

        result = await db.execute(
            select(Complaint)
            .where(
                Complaint.id == complaint_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_customer_id(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Complaint]:

        result = await db.execute(
            select(Complaint)
            .where(
                Complaint.customer_id == customer_id
            )
            .order_by(
                Complaint.created_at.desc(),
                Complaint.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        complaint: Complaint,
    ) -> Complaint:

        db.add(complaint)

        await db.commit()
        await db.refresh(complaint)

        return complaint