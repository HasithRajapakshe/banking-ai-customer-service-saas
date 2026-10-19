import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


class AuditRepository:
    async def list_for_tenant(
        self, db: AsyncSession, tenant_id: uuid.UUID, *, limit: int, offset: int
    ) -> tuple[list[AuditLog], int]:
        """Newest first, scoped to one tenant."""
        rows = await db.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
        total = await db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.tenant_id == tenant_id))
        return list(rows.scalars().all()), int(total or 0)


audit_repository = AuditRepository()
