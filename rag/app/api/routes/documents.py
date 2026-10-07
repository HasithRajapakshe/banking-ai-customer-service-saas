import uuid
import tempfile
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.database import get_db
from app.models import Document, DocumentChunk
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/v1/rag/documents", tags=["RAG Documents"])

@router.post("")
async def upload_document(
    tenant_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content_type = file.content_type or "text/plain"
    ext = ".pdf" if "pdf" in content_type else ".txt"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content_bytes = await file.read()
        tmp.write(content_bytes)
        tmp_path = tmp.name

    try:
        if "pdf" in content_type:
            loader = PyPDFLoader(tmp_path)
        else:
            loader = TextLoader(tmp_path, encoding='utf-8')
        docs = loader.load()
    finally:
        os.unlink(tmp_path)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_documents(docs)

    doc = Document(
        tenant_id=tenant_id,
        title=file.filename or "Untitled",
        filename=file.filename or "unknown",
        content_type=content_type,
        category="general",
        chunk_count=len(chunks)
    )
    db.add(doc)
    await db.flush()

    if chunks:
        texts = [chunk.page_content for chunk in chunks]
        embeddings = await rag_service.get_embeddings_batch(texts)
        
        for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = DocumentChunk(
                document_id=doc.id,
                tenant_id=tenant_id,
                chunk_index=i,
                content=chunk_data.page_content,
                metadata_json=chunk_data.metadata,
                embedding=embedding
            )
            db.add(db_chunk)
            
    await db.commit()
    
    return {"success": True, "document_id": str(doc.id)}

@router.get("")
async def list_documents(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Document).where(Document.tenant_id == tenant_id, Document.status == "active")
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{document_id}")
async def get_document(document_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Document).where(Document.id == document_id, Document.tenant_id == tenant_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/{document_id}")
async def delete_document(document_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Document).where(Document.id == document_id, Document.tenant_id == tenant_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc.status = "deleted"
    await db.commit()
    return {"success": True}
