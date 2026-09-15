import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import verify_internal_api_key
from app.core.errors import BankingAdapterError
from app.factory import get_banking_provider
from app.schemas.complaint import ComplaintDTO, ComplaintStatusDTO


router = APIRouter(
    prefix="/api/v1/customers/{customer_id}/complaints",
    tags=["Complaints"],
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
    response_model=list[ComplaintDTO],
)
async def list_complaints(
    customer_id: uuid.UUID,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    provider = get_banking_provider()

    try:
        return await provider.list_complaints(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintDTO,
)
async def get_complaint(
    customer_id: uuid.UUID,
    complaint_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_complaint(
            customer_id=customer_id,
            complaint_id=complaint_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{complaint_id}/status",
    response_model=ComplaintStatusDTO,
)
async def get_complaint_status(
    customer_id: uuid.UUID,
    complaint_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_complaint_status(
            customer_id=customer_id,
            complaint_id=complaint_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.post(
    "",
    response_model=ComplaintDTO,
    status_code=201,
)
async def create_complaint(
    customer_id: uuid.UUID,
    complaint_data: dict,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.create_complaint(
            customer_id=customer_id,
            complaint_data=complaint_data,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)
