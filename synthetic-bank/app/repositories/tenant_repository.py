import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant


class TenantRepository:
    async def get_by_id(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> Tenant | None:
        result = await db.execute(
            select(Tenant).where(
                Tenant.id == tenant_id
            )
        )

        return result.scalar_one_or_none()