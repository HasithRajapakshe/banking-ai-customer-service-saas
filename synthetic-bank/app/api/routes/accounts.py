import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from app.schemas.account import (
    AccountBalanceResponse,
    AccountResponse,
)
from app.schemas.account_transaction import AccountTransactionResponse
from app.services.account_service import AccountService
from app.services.account_transaction_service import (
    AccountTransactionService,
)


router = APIRouter(
    prefix="/api/v1/accounts",
    tags=["Accounts"],
)

account_service = AccountService()
transaction_service = AccountTransactionService()


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
)
async def get_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    account = await account_service.get_account(
        db,
        account_id,
    )

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return account


@router.get(
    "/{account_id}/balance",
    response_model=AccountBalanceResponse,
)
async def get_account_balance(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    account = await account_service.get_account_balance(
        db,
        account_id,
    )

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return AccountBalanceResponse(
        account_id=account.id,
        account_number=account.account_number,
        currency=account.currency,
        current_balance=account.current_balance,
        available_balance=account.available_balance,
    )


@router.get(
    "/{account_id}/transactions",
    response_model=list[AccountTransactionResponse],
)
async def get_account_transactions(
    account_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    account = await account_service.get_account(
        db,
        account_id,
    )

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return await transaction_service.get_account_transactions(
        db,
        account_id,
        limit,
        offset,
    )