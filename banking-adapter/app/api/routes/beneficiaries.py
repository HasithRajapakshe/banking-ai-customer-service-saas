import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import verify_internal_api_key
from app.core.errors import BankingAdapterError
from app.factory import get_banking_provider
from app.schemas.beneficiary import BeneficiaryDTO


router = APIRouter(
    prefix="/api/v1/customers/{customer_id}/beneficiaries",
    tags=["Beneficiaries"],
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
    response_model=list[BeneficiaryDTO],
)
async def list_beneficiaries(
    customer_id: uuid.UUID,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    provider = get_banking_provider()

    try:
        return await provider.list_beneficiaries(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{beneficiary_id}",
    response_model=BeneficiaryDTO,
)
async def get_beneficiary(
    customer_id: uuid.UUID,
    beneficiary_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_beneficiary(
            customer_id=customer_id,
            beneficiary_id=beneficiary_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.post(
    "",
    response_model=BeneficiaryDTO,
    status_code=201,
)
async def create_beneficiary(
    customer_id: uuid.UUID,
    beneficiary_data: dict,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.create_beneficiary(
            customer_id=customer_id,
            beneficiary_data=beneficiary_data,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.post(
    "/{beneficiary_id}/deactivate",
    response_model=BeneficiaryDTO,
)
async def deactivate_beneficiary(
    customer_id: uuid.UUID,
    beneficiary_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.deactivate_beneficiary(
            customer_id=customer_id,
            beneficiary_id=beneficiary_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)
