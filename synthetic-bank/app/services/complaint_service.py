import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.complaint import ComplaintCreateRequest


class ComplaintService:

    def __init__(self):
        self.repository = ComplaintRepository()

    async def get_complaint(
        self,
        db: AsyncSession,
        complaint_id: uuid.UUID,
    ):
        return await self.repository.get_by_id(
            db,
            complaint_id,
        )

    async def get_customer_complaints(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self.repository.get_by_customer_id(
            db,
            customer_id,
            limit,
            offset,
        )

    async def create_complaint(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        data: ComplaintCreateRequest,
    ):
        now = datetime.now(timezone.utc)

        complaint = Complaint(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            complaint_number=(
                f"CMP-{uuid.uuid4().hex[:12].upper()}"
            ),
            category=data.category.strip(),
            priority=data.priority,
            subject=data.subject.strip(),
            description=data.description.strip(),
            status="open",
            assigned_to=None,
            resolved_at=None,
            created_at=now,
            updated_at=now,
        )

        return await self.repository.create(
            db,
            complaint,
        )