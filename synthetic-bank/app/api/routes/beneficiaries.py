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
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def list_customer_beneficiaries(
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

    return await beneficiary_service.get_customer_beneficiaries(
        db,
        trusted_customer_id,
        tenant_id,
        limit,
        offset,
    )


@router.post(
    "/customer/{customer_id}",
    response_model=BeneficiaryResponse,
    status_code=201,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def create_beneficiary(
    customer_id: uuid.UUID,
    data: BeneficiaryCreateRequest,
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

    return await beneficiary_service.create_beneficiary(
        db,
        trusted_customer_id,
        tenant_id,
        data,
    )


@router.get(
    "/{beneficiary_id}",
    response_model=BeneficiaryResponse,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_beneficiary(
    beneficiary_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    beneficiary = await beneficiary_service.get_beneficiary(
        db,
        beneficiary_id,
        tenant_id,
        customer_id,
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
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def deactivate_beneficiary(
    beneficiary_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    beneficiary = (
        await beneficiary_service.deactivate_beneficiary(
            db,
            beneficiary_id,
            tenant_id,
            customer_id,
        )
    )

    if beneficiary is None:
        raise HTTPException(
            status_code=404,
            detail="Beneficiary not found",
        )

    return beneficiary
