import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db

from app.core.config import settings
from app.core.errors import AppError
from app.repositories.tenant_repository import TenantRepository


tenant_repository = TenantRepository()


async def require_configured_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    tenant = await tenant_repository.get_by_id(
        db,
        settings.tenant_id,
    )

    if tenant is None:
        raise AppError(
            status_code=500,
            code="CONFIGURED_TENANT_NOT_FOUND",
            message="Configured bank tenant was not found",
        )

    if tenant.status != "active":
        raise AppError(
            status_code=503,
            code="CONFIGURED_TENANT_INACTIVE",
            message="Configured bank tenant is not active",
        )

    if tenant.tenant_code != settings.bank_code:
        raise AppError(
            status_code=500,
            code="BANK_CONFIGURATION_MISMATCH",
            message="Configured bank code does not match tenant",
        )

    request.state.tenant_id = tenant.id
    request.state.bank_code = tenant.tenant_code

    return tenant.id