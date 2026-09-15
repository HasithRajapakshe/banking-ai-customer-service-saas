import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import verify_internal_api_key
from app.core.errors import BankingAdapterError
from app.factory import get_banking_provider
from app.schemas.payment import PaymentDTO, PaymentStatusDTO


router = APIRouter(
    prefix="/api/v1/customers/{customer_id}/payments",
    tags=["Payments"],
    dependencies=[Depends(verify_internal_api_key)],
)


def get_correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "") or ""


def raise_adapter_error(exc: BankingAdapterError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
            "correlation_id": exc.correlation_id,
        },
    )


@router.get(
    "",
    response_model=list[PaymentDTO],
)
async def list_payments(
    customer_id: uuid.UUID,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    provider = get_banking_provider()

    try:
        return await provider.list_payments(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{payment_id}",
    response_model=PaymentDTO,
)
async def get_payment(
    customer_id: uuid.UUID,
    payment_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_payment(
            customer_id=customer_id,
            payment_id=payment_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{payment_id}/status",
    response_model=PaymentStatusDTO,
)
async def get_payment_status(
    customer_id: uuid.UUID,
    payment_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_payment_status(
            customer_id=customer_id,
            payment_id=payment_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.post(
    "",
    response_model=PaymentDTO,
    status_code=201,
)
async def create_payment(
    customer_id: uuid.UUID,
    payment_data: dict,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.create_payment(
            customer_id=customer_id,
            payment_data=payment_data,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.post(
    "/{payment_id}/cancel",
    response_model=PaymentDTO,
)
async def cancel_payment(
    customer_id: uuid.UUID,
    payment_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.cancel_payment(
            customer_id=customer_id,
            payment_id=payment_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)
