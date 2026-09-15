import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import verify_internal_api_key
from app.core.errors import BankingAdapterError
from app.factory import get_banking_provider
from app.schemas.account import AccountBalanceDTO, AccountDTO
from app.schemas.transaction import AccountTransactionDTO


router = APIRouter(
    prefix="/api/v1/customers/{customer_id}/accounts",
    tags=["Accounts"],
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
    response_model=list[AccountDTO],
)
async def list_accounts(
    customer_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_accounts(
            customer_id=customer_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{account_id}",
    response_model=AccountDTO,
)
async def get_account(
    customer_id: uuid.UUID,
    account_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_account(
            customer_id=customer_id,
            account_id=account_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{account_id}/balance",
    response_model=AccountBalanceDTO,
)
async def get_account_balance(
    customer_id: uuid.UUID,
    account_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_balance(
            customer_id=customer_id,
            account_id=account_id,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)


@router.get(
    "/{account_id}/transactions",
    response_model=list[AccountTransactionDTO],
)
async def get_account_transactions(
    customer_id: uuid.UUID,
    account_id: uuid.UUID,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    provider = get_banking_provider()

    try:
        return await provider.get_account_transactions(
            customer_id=customer_id,
            account_id=account_id,
            limit=limit,
            offset=offset,
            correlation_id=get_correlation_id(request),
        )

    except BankingAdapterError as exc:
        raise_adapter_error(exc)