import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentCreateRequest


class PaymentService:

    def __init__(self):
        self.repository = PaymentRepository()

    async def get_payment(
        self,
        db: AsyncSession,
        payment_id: uuid.UUID,
    ):
        return await self.repository.get_by_id(
            db,
            payment_id,
        )

    async def get_customer_payments(
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

    async def create_payment(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        data: PaymentCreateRequest,
    ):
        if data.idempotency_key:
            existing = await self.repository.get_by_idempotency_key(
                db,
                data.idempotency_key,
            )

            if existing:
                return existing

        now = datetime.now(timezone.utc)

        payment = Payment(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            source_account_id=data.source_account_id,
            beneficiary_id=data.beneficiary_id,
            payment_number=f"PAY-{uuid.uuid4().hex[:12].upper()}",
            amount=data.amount,
            currency=data.currency.upper(),
            payment_reference=data.payment_reference,
            status="pending",
            idempotency_key=data.idempotency_key,
            requested_at=now,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )

        return await self.repository.create(
            db,
            payment,
        )

    async def cancel_payment(
        self,
        db: AsyncSession,
        payment_id: uuid.UUID,
    ):
        payment = await self.repository.get_by_id(
            db,
            payment_id,
        )

        if payment is None:
            return None

        if payment.status not in {
            "pending",
            "processing",
        }:
            return payment

        return await self.repository.cancel(
            db,
            payment,
        )