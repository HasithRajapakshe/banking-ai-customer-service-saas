import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db

from app.models.customer import Customer
from app.schemas.beneficiary import (
    BeneficiaryCreateRequest,
    BeneficiaryResponse,
)
from app.services.beneficiary_service import BeneficiaryService


router = APIRouter(
    prefix="/api/v1/beneficiaries",
    tags=["Beneficiaries"],
)

beneficiary_service = BeneficiaryService()


@router.get(
    "/customer/{customer_id}",
    response_model=list[BeneficiaryResponse],
)
async def list_customer_beneficiaries(
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
    return await beneficiary_service.get_customer_beneficiaries(
        db,
        customer_id,
        limit,
        offset,
    )


@router.post(
    "/customer/{customer_id}",
    response_model=BeneficiaryResponse,
    status_code=201,
)
async def create_beneficiary(
    customer_id: uuid.UUID,
    data: BeneficiaryCreateRequest,
    db: AsyncSession = Depends(get_db),
):
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

    return await beneficiary_service.create_beneficiary(
        db,
        customer_id,
        customer.tenant_id,
        data,
    )


@router.get(
    "/{beneficiary_id}",
    response_model=BeneficiaryResponse,
)
async def get_beneficiary(
    beneficiary_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    beneficiary = await beneficiary_service.get_beneficiary(
        db,
        beneficiary_id,
    )

    if beneficiary is None:
        raise HTTPException(
            status_code=404,
            detail="Beneficiary not found",
        )

    return beneficiary


@router.delete(
    "/{beneficiary_id}",
    response_model=BeneficiaryResponse,
)
async def deactivate_beneficiary(
    beneficiary_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    beneficiary = await beneficiary_service.deactivate_beneficiary(
        db,
        beneficiary_id,
    )

    if beneficiary is None:
        raise HTTPException(
            status_code=404,
            detail="Beneficiary not found",
        )

    return beneficiary
