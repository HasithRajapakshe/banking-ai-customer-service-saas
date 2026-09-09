import uuid

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db

from app.core.config import settings
from app.core.errors import AppError
from app.models.customer import Customer


CUSTOMER_ID_HEADER = "X-Customer-ID"


async def require_customer_context(
    request: Request,
    x_customer_id: str | None = Header(
        default=None,
        alias=CUSTOMER_ID_HEADER,
    ),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    # -------------------------
    # 1. Customer ID required
    # -------------------------

    if not x_customer_id:
        raise AppError(
            status_code=400,
            code="CUSTOMER_ID_REQUIRED",
            message="Customer ID is required",
        )

    # -------------------------
    # 2. Validate UUID format
    # -------------------------

    try:
        customer_id = uuid.UUID(x_customer_id)
    except ValueError:
        raise AppError(
            status_code=400,
            code="INVALID_CUSTOMER_ID",
            message="Customer ID must be a valid UUID",
        )

    # -------------------------
    # 3. Find customer in the
    #    configured bank only
    # -------------------------

    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == settings.tenant_id,
        )
    )

    customer = result.scalar_one_or_none()

    if customer is None:
        raise AppError(
            status_code=404,
            code="CUSTOMER_NOT_FOUND",
            message="Customer not found",
        )

    # -------------------------
    # 4. Validate customer status
    # -------------------------

    if customer.status != "active":
        raise AppError(
            status_code=403,
            code="CUSTOMER_INACTIVE",
            message="Customer is not active",
        )

    # -------------------------
    # 5. Store trusted context
    # -------------------------

    request.state.customer_id = customer.id

    return customer.id