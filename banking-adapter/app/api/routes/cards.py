import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import verify_internal_api_key
from app.core.errors import BankingAdapterError
from app.factory import get_banking_provider
from app.schemas.card import CardDTO, CardTransactionDTO


router = APIRouter(
    prefix="/api/v1/customers/{customer_id}/cards",
    tags=["Cards"],
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
    "/{card_id}",
    response_model=CardDTO,
)
async def get_card(
    customer_id: uuid.UUID,
    card_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_card(
            customer_id=customer_id,
            card_id=card_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{card_id}/transactions",
    response_model=list[CardTransactionDTO],
)
async def get_card_transactions(
    customer_id: uuid.UUID,
    card_id: uuid.UUID,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    provider = get_banking_provider()

    try:
        return await provider.get_card_transactions(
            customer_id=customer_id,
            card_id=card_id,
            limit=limit,
            offset=offset,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.post(
    "/{card_id}/block",
    response_model=CardDTO,
)
async def block_card(
    customer_id: uuid.UUID,
    card_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.block_card(
            customer_id=customer_id,
            card_id=card_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)
