import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db

from app.schemas.loan import (
    LoanResponse,
    LoanStatusResponse,
)
from app.schemas.loan_payment import LoanPaymentResponse
from app.services.loan_service import LoanService


router = APIRouter(
    prefix="/api/v1/loans",
    tags=["Loans"],
)

loan_service = LoanService()


@router.get(
    "/customer/{customer_id}",
    response_model=list[LoanResponse],
)
async def list_customer_loans(
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
    return await loan_service.get_customer_loans(
        db,
        customer_id,
        limit,
        offset,
    )


@router.get(
    "/{loan_id}/payments",
    response_model=list[LoanPaymentResponse],
)
async def get_loan_payments(
    loan_id: uuid.UUID,
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
    loan = await loan_service.get_loan(
        db,
        loan_id,
    )

    if loan is None:
        raise HTTPException(
            status_code=404,
            detail="Loan not found",
        )

    return await loan_service.get_loan_payments(
        db,
        loan_id,
        limit,
        offset,
    )


@router.get(
    "/{loan_id}/status",
    response_model=LoanStatusResponse,
)
async def get_loan_status(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    loan = await loan_service.get_loan(
        db,
        loan_id,
    )

    if loan is None:
        raise HTTPException(
            status_code=404,
            detail="Loan not found",
        )

    return LoanStatusResponse(
        id=loan.id,
        loan_number=loan.loan_number,
        status=loan.status,
        principal_amount=loan.principal_amount,
        outstanding_amount=loan.outstanding_amount,
        interest_rate=loan.interest_rate,
        currency=loan.currency,
        maturity_date=loan.maturity_date,
    )


@router.get(
    "/{loan_id}",
    response_model=LoanResponse,
)
async def get_loan(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    loan = await loan_service.get_loan(
        db,
        loan_id,
    )

    if loan is None:
        raise HTTPException(
            status_code=404,
            detail="Loan not found",
        )

    return loan