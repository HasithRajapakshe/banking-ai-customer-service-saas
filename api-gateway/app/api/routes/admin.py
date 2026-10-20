import datetime
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_roles, require_permission
from app.core.config import settings
from app.core.database import get_db
from app.core.internal_token import internal_headers, sign_internal_token
from app.models import AppUser, Role
from app.repositories.audit_repository import audit_repository

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


def _rag_headers(request: Request, user: AppUser, roles: list[Role]) -> dict[str, str]:
    # RAG takes the tenant only from this token.
    token = sign_internal_token(user, [r.role_code for r in roles])
    correlation_id = getattr(request.state, "correlation_id", None) or str(uuid.uuid4())
    return internal_headers(token, correlation_id)


@router.post("/rag/documents")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: AppUser = Depends(require_permission("knowledge.manage")),
    roles: list[Role] = Depends(get_current_user_roles),
):
    """Proxy document upload to the RAG service for the admin's tenant."""
    async with httpx.AsyncClient() as client:
        try:
            content = await file.read()
            response = await client.post(
                f"{settings.rag_base_url}/api/v1/rag/documents",
                files={"file": (file.filename, content, file.content_type)},
                headers=_rag_headers(request, current_user, roles),
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"RAG error: {exc.response.text}")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Failed to communicate with RAG Service: {str(exc)}")


@router.get("/rag/documents")
async def list_documents(
    request: Request,
    current_user: AppUser = Depends(require_permission("knowledge.manage")),
    roles: list[Role] = Depends(get_current_user_roles),
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.rag_base_url}/api/v1/rag/documents",
                headers=_rag_headers(request, current_user, roles),
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"RAG error: {exc.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Failed to communicate with RAG Service")


class AuditEntry(BaseModel):
    id: uuid.UUID
    created_at: datetime.datetime
    action: str
    success: bool
    actor_user_id: uuid.UUID | None
    resource_type: str | None
    resource_id: uuid.UUID | None
    correlation_id: str | None
    metadata: dict[str, Any]


class AuditPage(BaseModel):
    items: list[AuditEntry]
    total: int
    limit: int
    offset: int


@router.get("/audit", response_model=AuditPage)
async def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: AppUser = Depends(require_permission("audit.read")),
    db: AsyncSession = Depends(get_db),
):
    """Audit trail for the admin's own tenant, newest first."""
    rows, total = await audit_repository.list_for_tenant(db, current_user.tenant_id, limit=limit, offset=offset)
    items = [
        AuditEntry(
            id=row.id, created_at=row.created_at, action=row.action, success=row.success,
            actor_user_id=row.actor_user_id, resource_type=row.resource_type, resource_id=row.resource_id,
            correlation_id=row.correlation_id, metadata=row.metadata_json or {},
        )
        for row in rows
    ]
    return AuditPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/users")
async def get_users(
    current_user: AppUser = Depends(require_permission("users.manage")),
):
    # Not implemented yet (see docs/IMPLEMENTATION_STATUS.md).
    return []
