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
from app.schemas.complaint import (
    ComplaintCreateRequest,
    ComplaintResponse,
    ComplaintStatusResponse,
)
from app.services.complaint_service import ComplaintService


router = APIRouter(
    prefix="/api/v1/complaints",
    tags=["Complaints"],
)

complaint_service = ComplaintService()


@router.get(
    "/customer/{customer_id}",
    response_model=list[ComplaintResponse],
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def list_customer_complaints(
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

    return await complaint_service.get_customer_complaints(
        db,
        trusted_customer_id,
        tenant_id,
        limit,
        offset,
    )


@router.post(
    "/customer/{customer_id}",
    response_model=ComplaintResponse,
    status_code=201,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def create_complaint(
    customer_id: uuid.UUID,
    data: ComplaintCreateRequest,
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

    return await complaint_service.create_complaint(
        db,
        trusted_customer_id,
        tenant_id,
        data,
    )


@router.get(
    "/{complaint_id}/status",
    response_model=ComplaintStatusResponse,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_complaint_status(
    complaint_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    complaint = await complaint_service.get_complaint(
        db,
        complaint_id,
        tenant_id,
        customer_id,
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    return ComplaintStatusResponse(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        status=complaint.status,
        priority=complaint.priority,
        assigned_to=complaint.assigned_to,
        resolved_at=complaint.resolved_at,
        updated_at=complaint.updated_at,
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_complaint(
    complaint_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    complaint = await complaint_service.get_complaint(
        db,
        complaint_id,
        tenant_id,
        customer_id,
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    return complaint