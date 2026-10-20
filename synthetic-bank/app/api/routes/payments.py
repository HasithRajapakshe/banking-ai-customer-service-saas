import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db

from app.core.customer_context import require_customer_context
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


# =========================
# Customer Payment List
# =========================

@router.get(
    "/customer/{customer_id}",
    response_model=list[PaymentResponse],
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def list_customer_payments(
    customer_id: uuid.UUID,
    request: Request,
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
    trusted_customer_id = request.state.customer_id
    tenant_id = request.state.tenant_id

    if customer_id != trusted_customer_id:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return await payment_service.get_customer_payments(
        db,
        trusted_customer_id,
        tenant_id,
        limit,
        offset,
    )


# =========================
# Create Payment
# =========================

@router.post(
    "/customer/{customer_id}",
    response_model=PaymentResponse,
    status_code=201,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def create_payment(
    customer_id: uuid.UUID,
    data: PaymentCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    trusted_customer_id = request.state.customer_id
    tenant_id = request.state.tenant_id

    if customer_id != trusted_customer_id:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return await payment_service.create_payment(
        db,
        trusted_customer_id,
        tenant_id,
        data,
    )


# =========================
# Payment Status
# =========================

@router.get(
    "/{payment_id}/status",
    response_model=PaymentResponse,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_payment_status(
    payment_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    payment = await payment_service.get_payment(
        db,
        payment_id,
        tenant_id,
        customer_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment


# =========================
# Cancel Payment
# =========================

@router.post(
    "/{payment_id}/cancel",
    response_model=PaymentResponse,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def cancel_payment(
    payment_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    payment = await payment_service.cancel_payment(
        db,
        payment_id,
        tenant_id,
        customer_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment


# =========================
# Get Payment
# =========================

@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_payment(
    payment_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    payment = await payment_service.get_payment(
        db,
        payment_id,
        tenant_id,
        customer_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment