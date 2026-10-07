import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Document, DocumentChunk
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


@router.get("/search")
async def search_documents(
    query: str,
    tenant_id: uuid.UUID,
    limit: int = Query(default=5, ge=1, le=20),
    similarity_threshold: float = Query(default=0.7, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for document chunks relevant to the query using vector similarity.
    """
    # 1. Get embedding for the query
    try:
        query_embedding = await rag_service.get_embedding(query)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding for query: {str(exc)}",
        )

    # 2. Vector search using pgvector
    # L2 distance or Cosine distance. pgvector uses <=> for cosine distance.
    stmt = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.tenant_id == tenant_id,
            Document.status == "active"
        )
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()
    
    # In a real implementation, you might filter out results below the similarity threshold.
    # We can do this in Python or by adding a WHERE clause using the cosine_distance operator.
    
    results = []
    for chunk, doc in rows:
        results.append({
            "chunk_id": str(chunk.id),
            "document_id": str(doc.id),
            "title": doc.title,
            "filename": doc.filename,
            "category": doc.category,
            "content": chunk.content,
            "metadata": chunk.metadata_json,
        })
        
    return {
        "success": True,
        "query": query,
        "results": results
    }
