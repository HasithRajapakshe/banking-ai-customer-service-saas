import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db

from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentResponse,
)
from app.services.payment_service import PaymentService


router = APIRouter(
    prefix="/api/v1/payments",
    tags=["Payments"],
)

payment_service = PaymentService()


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    payment = await payment_service.get_payment(
        db,
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment


@router.get(
    "/customer/{customer_id}",
    response_model=list[PaymentResponse],
)
async def list_customer_payments(
    customer_id: uuid.UUID,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.get_customer_payments(
        db,
        customer_id,
        limit,
        offset,
    )


@router.post(
    "/customer/{customer_id}",
    response_model=PaymentResponse,
    status_code=201,
)
async def create_payment(
    customer_id: uuid.UUID,
    data: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    # Temporary synthetic-bank tenant resolution.
    # Tenant validation will move into the security layer later.
    from sqlalchemy import select
    from app.models.customer import Customer

    result = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
    )

    customer = result.scalar_one_or_none()

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return await payment_service.create_payment(
        db,
        customer_id,
        customer.tenant_id,
        data,
    )


@router.get(
    "/{payment_id}/status",
    response_model=PaymentResponse,
)
async def get_payment_status(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    payment = await payment_service.get_payment(
        db,
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment


@router.post(
    "/{payment_id}/cancel",
    response_model=PaymentResponse,
)
async def cancel_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    payment = await payment_service.cancel_payment(
        db,
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if payment.status not in {
        "cancelled",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Payment cannot be cancelled "
                f"from status '{payment.status}'"
            ),
        )

    return payment