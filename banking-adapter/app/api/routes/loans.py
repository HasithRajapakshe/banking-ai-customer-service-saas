import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import verify_internal_api_key
from app.core.errors import BankingAdapterError
from app.factory import get_banking_provider
from app.schemas.loan import LoanDTO, LoanPaymentDTO, LoanStatusDTO


router = APIRouter(
    prefix="/api/v1/customers/{customer_id}/loans",
    tags=["Loans"],
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
    response_model=list[LoanDTO],
)
async def list_loans(
    customer_id: uuid.UUID,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    provider = get_banking_provider()

    try:
        return await provider.list_loans(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{loan_id}",
    response_model=LoanDTO,
)
async def get_loan(
    customer_id: uuid.UUID,
    loan_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_loan(
            customer_id=customer_id,
            loan_id=loan_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{loan_id}/status",
    response_model=LoanStatusDTO,
)
async def get_loan_status(
    customer_id: uuid.UUID,
    loan_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_loan_status(
            customer_id=customer_id,
            loan_id=loan_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{loan_id}/payments",
    response_model=list[LoanPaymentDTO],
)
async def get_loan_payments(
    customer_id: uuid.UUID,
    loan_id: uuid.UUID,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    provider = get_banking_provider()

    try:
        return await provider.get_loan_payments(
            customer_id=customer_id,
            loan_id=loan_id,
            limit=limit,
            offset=offset,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)
