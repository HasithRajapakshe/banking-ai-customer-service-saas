import hashlib
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.internal_auth import InternalIdentity, require_internal_identity, tenant_from_token
from app.models import Document, DocumentChunk, DocumentVersion
from app.schemas import DocumentResponse, DocumentUploadResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/v1/rag/documents", tags=["RAG Documents"])

UPLOADED_DOCUMENT_TYPE = "uploaded"


def _sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _document_key(filename: str) -> str:
    stem = os.path.splitext(filename)[0].lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")[:80] or "document"
    return f"{slug}-{uuid.uuid4().hex[:8]}"


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    tenant_id: uuid.UUID | None = Form(default=None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    identity: InternalIdentity = Depends(require_internal_identity),
):
    tenant_id = tenant_from_token(identity, tenant_id)
    content_type = file.content_type or "text/plain"
    is_pdf = "pdf" in content_type
    content_bytes = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf" if is_pdf else ".txt") as tmp:
        tmp.write(content_bytes)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path) if is_pdf else TextLoader(tmp_path, encoding="utf-8")
        docs = loader.load()
    finally:
        os.unlink(tmp_path)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_documents(docs)

    filename = file.filename or "untitled"
    now = datetime.now(timezone.utc)

    doc = Document(
        tenant_id=tenant_id,
        document_key=_document_key(filename),
        title=filename,
        document_type=UPLOADED_DOCUMENT_TYPE,
        status="published",
    )
    db.add(doc)
    await db.flush()

    version = DocumentVersion(
        tenant_id=tenant_id,
        document_id=doc.id,
        version_number=1,
        content_hash=_sha256(content_bytes),
        status="published",
        published_at=now,
    )
    db.add(version)
    await db.flush()

    if chunks:
        texts = [chunk.page_content for chunk in chunks]
        embeddings = await rag_service.get_embeddings_batch(texts)

        for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
            db.add(
                DocumentChunk(
                    tenant_id=tenant_id,
                    document_id=doc.id,
                    document_version_id=version.id,
                    chunk_index=i,
                    content=chunk_data.page_content,
                    content_hash=_sha256(chunk_data.page_content),
                    metadata_json={**chunk_data.metadata, "filename": filename},
                    embedding=embedding,
                )
            )

    await db.commit()

    return DocumentUploadResponse(
        success=True,
        document_id=doc.id,
        document_version_id=version.id,
        chunk_count=len(chunks),
    )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    identity: InternalIdentity = Depends(require_internal_identity),
):
    tenant_id = tenant_from_token(identity, tenant_id)
    stmt = select(Document).where(Document.tenant_id == tenant_id, Document.status == "published")
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    identity: InternalIdentity = Depends(require_internal_identity),
):
    tenant_id = tenant_from_token(identity, tenant_id)
    stmt = select(Document).where(Document.id == document_id, Document.tenant_id == tenant_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    identity: InternalIdentity = Depends(require_internal_identity),
):
    tenant_id = tenant_from_token(identity, tenant_id)
    stmt = select(Document).where(Document.id == document_id, Document.tenant_id == tenant_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "archived"
    await db.commit()
    return {"success": True}
