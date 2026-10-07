import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, require_permission
from app.core.config import settings
from app.core.database import get_db
from app.models import AppUser

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

@router.post("/rag/documents")
async def upload_document(
    file: UploadFile = File(...),
    current_user: AppUser = Depends(require_permission("knowledge.manage")),
):
    """Proxy document upload to RAG service, securely injecting the tenant_id."""
    async with httpx.AsyncClient() as client:
        try:
            content = await file.read()
            files = {"file": (file.filename, content, file.content_type)}
            data = {"tenant_id": str(current_user.tenant_id)}
            
            response = await client.post(
                f"{settings.rag_base_url}/api/v1/rag/documents",
                files=files,
                data=data,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"RAG error: {exc.response.text}"
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to communicate with RAG Service: {str(exc)}"
            )

@router.get("/rag/documents")
async def list_documents(
    current_user: AppUser = Depends(require_permission("knowledge.manage")),
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.rag_base_url}/api/v1/rag/documents?tenant_id={str(current_user.tenant_id)}",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"RAG error: {exc.response.text}")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail="Failed to communicate with RAG Service")

@router.get("/audit")
async def get_audit_logs(
    current_user: AppUser = Depends(require_permission("audit.read")),
):
    # Dummy implementation for now, should read from DB
    return []

@router.get("/users")
async def get_users(
    current_user: AppUser = Depends(require_permission("users.manage")),
):
    # Dummy implementation
    return []
