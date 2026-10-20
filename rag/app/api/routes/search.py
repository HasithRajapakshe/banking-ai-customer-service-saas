import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.internal_auth import InternalIdentity, require_internal_identity, tenant_from_token
from app.models import Document, DocumentChunk
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


@router.get("/search")
async def search_documents(
    query: str,
    tenant_id: uuid.UUID | None = None,
    limit: int = Query(default=5, ge=1, le=20),
    similarity_threshold: float | None = Query(default=None, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    identity: InternalIdentity = Depends(require_internal_identity),
):
    """
    Search published document chunks for the tenant by cosine similarity.

    Only chunks with similarity >= similarity_threshold are returned
    (default: settings.search_similarity_threshold), best match first.
    """
    tenant_id = tenant_from_token(identity, tenant_id)
    threshold = (
        similarity_threshold
        if similarity_threshold is not None
        else settings.search_similarity_threshold
    )

    try:
        query_embedding = await rag_service.get_embedding(query)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding for query: {str(exc)}",
        )

    # pgvector's <=> is cosine distance; similarity = 1 - distance.
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(DocumentChunk, Document, distance.label("distance"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.tenant_id == tenant_id,
            Document.tenant_id == tenant_id,
            Document.status == "published",
            DocumentChunk.embedding.is_not(None),
            distance <= 1.0 - threshold,
        )
        .order_by(distance)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    results = [
        {
            "chunk_id": str(chunk.id),
            "document_id": str(doc.id),
            "document_key": doc.document_key,
            "title": doc.title,
            "document_type": doc.document_type,
            "content": chunk.content,
            "metadata": chunk.metadata_json,
            "similarity": round(1.0 - float(dist), 4),
        }
        for chunk, doc, dist in rows
    ]

    return {
        "success": True,
        "query": query,
        "similarity_threshold": threshold,
        "results": results,
    }
