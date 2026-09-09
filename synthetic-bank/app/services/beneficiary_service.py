import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.beneficiary import Beneficiary
from app.repositories.beneficiary_repository import BeneficiaryRepository
from app.schemas.beneficiary import BeneficiaryCreateRequest


class BeneficiaryService:

    def __init__(self):
        self.repository = BeneficiaryRepository()

    @staticmethod
    def mask_account_number(account_number: str) -> str:
        cleaned = account_number.strip()

        if len(cleaned) <= 4:
            return cleaned

        return "*" * (len(cleaned) - 4) + cleaned[-4:]

    async def get_beneficiary(
        self,
        db: AsyncSession,
        beneficiary_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ):
        return await self.repository.get_by_id(
            db,
            beneficiary_id,
            tenant_id,
            customer_id,
        )

    async def get_customer_beneficiaries(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self.repository.get_by_customer_id(
            db,
            customer_id,
            tenant_id,
            limit,
            offset,
        )

    async def create_beneficiary(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        data: BeneficiaryCreateRequest,
    ):
        now = datetime.now(timezone.utc)

        beneficiary = Beneficiary(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            beneficiary_number=(
                f"BEN-{uuid.uuid4().hex[:12].upper()}"
            ),
            beneficiary_name=data.beneficiary_name.strip(),
            bank_name=(
                data.bank_name.strip()
                if data.bank_name
                else None
            ),
            account_number_masked=self.mask_account_number(
                data.account_number
            ),
            status="active",
            created_at=now,
            updated_at=now,
        )

        return await self.repository.create(
            db,
            beneficiary,
        )

    async def deactivate_beneficiary(
        self,
        db: AsyncSession,
        beneficiary_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ):
        beneficiary = await self.repository.get_by_id(
            db,
            beneficiary_id,
            tenant_id,
            customer_id,
        )

        if beneficiary is None:
            return None

        return await self.repository.deactivate(
            db,
            beneficiary,
        )
