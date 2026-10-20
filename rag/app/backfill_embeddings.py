"""Embed document chunks that have no embedding yet.

The synthetic seed inserts knowledge chunks with NULL embeddings (the SQL
seed has no embedding model). Run once after migrations:

    python -m app.backfill_embeddings

Idempotent: only chunks WHERE embedding IS NULL are touched, so re-running
is a no-op. Uses the configured provider (EMBEDDING_PROVIDER).
"""

import asyncio
import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models import DocumentChunk
from app.services.rag_service import rag_service

logger = logging.getLogger("rag.backfill")

BATCH_SIZE = 100


async def backfill_missing_embeddings(session: AsyncSession, batch_size: int = BATCH_SIZE) -> int:
    """Embed all chunks lacking an embedding. Returns the number of chunks updated."""
    total = 0
    while True:
        result = await session.execute(
            select(DocumentChunk.id, DocumentChunk.content)
            .where(DocumentChunk.embedding.is_(None))
            .order_by(DocumentChunk.id)
            .limit(batch_size)
        )
        rows = result.all()
        if not rows:
            return total

        vectors = await rag_service.get_embeddings_batch([content for _, content in rows])
        for (chunk_id, _), vector in zip(rows, vectors):
            await session.execute(
                update(DocumentChunk).where(DocumentChunk.id == chunk_id).values(embedding=vector)
            )
        await session.commit()
        total += len(rows)


async def main() -> None:
    try:
        async with AsyncSessionLocal() as session:
            count = await backfill_missing_embeddings(session)
        print(f"Embedded {count} document chunk(s) that had no embedding.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
