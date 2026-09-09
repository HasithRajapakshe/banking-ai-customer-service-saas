import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.account import Account
from app.models.beneficiary import Beneficiary
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
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ):
        return await self.repository.get_by_id(
            db,
            payment_id,
            tenant_id,
            customer_id,
        )

    async def get_customer_payments(
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

    async def create_payment(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        data: PaymentCreateRequest,
    ):
        # =========================
        # Idempotency
        # =========================

        if data.idempotency_key:
            existing_payment = (
                await self.repository.get_by_idempotency_key(
                    db,
                    data.idempotency_key,
                    tenant_id,
                    customer_id,
                )
            )

            if existing_payment is not None:
                return existing_payment

        # =========================
        # Validate Source Account
        # =========================

        account_result = await db.execute(
            select(Account).where(
                Account.id == data.source_account_id,
                Account.tenant_id == tenant_id,
                Account.customer_id == customer_id,
            )
        )

        source_account = account_result.scalar_one_or_none()

        if source_account is None:
            raise AppError(
                status_code=404,
                code="SOURCE_ACCOUNT_NOT_FOUND",
                message="Source account not found",
            )

        if source_account.status != "active":
            raise AppError(
                status_code=400,
                code="SOURCE_ACCOUNT_NOT_ACTIVE",
                message="Source account is not active",
            )

        # =========================
        # Validate Beneficiary
        # =========================

        beneficiary_result = await db.execute(
            select(Beneficiary).where(
                Beneficiary.id == data.beneficiary_id,
                Beneficiary.tenant_id == tenant_id,
                Beneficiary.customer_id == customer_id,
                Beneficiary.status == "active",
            )
        )

        beneficiary = beneficiary_result.scalar_one_or_none()

        if beneficiary is None:
            raise AppError(
                status_code=404,
                code="BENEFICIARY_NOT_FOUND",
                message="Beneficiary not found",
            )

        # =========================
        # Create Payment
        # =========================

        now = datetime.now(timezone.utc)

        payment = Payment(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            source_account_id=source_account.id,
            beneficiary_id=beneficiary.id,
            payment_number=(
                f"PAY-{uuid.uuid4().hex[:12].upper()}"
            ),
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
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ):
        payment = await self.repository.get_by_id(
            db,
            payment_id,
            tenant_id,
            customer_id,
        )

        if payment is None:
            return None

        if payment.status not in {
            "pending",
            "processing",
        }:
            raise AppError(
                status_code=409,
                code="PAYMENT_CANNOT_BE_CANCELLED",
                message=(
                    "Only pending or processing payments "
                    "can be cancelled"
                ),
            )

        return await self.repository.cancel(
            db,
            payment,
        )