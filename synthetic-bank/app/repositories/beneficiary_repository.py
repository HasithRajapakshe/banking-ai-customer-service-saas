import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.beneficiary import Beneficiary


class BeneficiaryRepository:

    async def get_by_id(
        self,
        db: AsyncSession,
        beneficiary_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Beneficiary | None:

        result = await db.execute(
            select(Beneficiary).where(
                Beneficiary.id == beneficiary_id,
                Beneficiary.tenant_id == tenant_id,
                Beneficiary.customer_id == customer_id,
                Beneficiary.status != "deleted",
            )
        )

        return result.scalar_one_or_none()

    async def get_by_customer_id(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Beneficiary]:

        result = await db.execute(
            select(Beneficiary)
            .where(
                Beneficiary.customer_id == customer_id,
                Beneficiary.tenant_id == tenant_id,
                Beneficiary.status != "deleted",
            )
            .order_by(
                Beneficiary.created_at.desc(),
                Beneficiary.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        beneficiary: Beneficiary,
    ) -> Beneficiary:

        db.add(beneficiary)

        await db.commit()
        await db.refresh(beneficiary)

        return beneficiary

    async def deactivate(
        self,
        db: AsyncSession,
        beneficiary: Beneficiary,
    ) -> Beneficiary:

        beneficiary.status = "deleted"
        beneficiary.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(beneficiary)

        return beneficiary
