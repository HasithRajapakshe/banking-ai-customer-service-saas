import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from app.backfill_embeddings import backfill_missing_embeddings
from app.models import EMBEDDING_DIMENSIONS
from app.services.rag_service import MockEmbeddings


def compiled(stmt) -> str:
    return str(stmt.compile(dialect=postgresql.dialect()))


def session_returning(*batches):
    """Session whose SELECTs return the given batches, then nothing."""
    session = AsyncMock()
    selects = iter([*batches, []])

    async def execute(stmt):
        result = MagicMock()
        if compiled(stmt).lstrip().upper().startswith("SELECT"):
            result.all.return_value = next(selects)
        return result

    session.execute.side_effect = execute
    return session


@pytest.mark.asyncio(loop_scope="function")
async def test_backfill_embeds_only_chunks_without_embedding():
    rows = [(uuid.uuid4(), "Lost or stolen card procedure"), (uuid.uuid4(), "KYC requirements")]
    session = session_returning(rows)

    count = await backfill_missing_embeddings(session)

    assert count == 2
    statements = [call.args[0] for call in session.execute.await_args_list]
    select_sql = compiled(statements[0])
    assert "embedding IS NULL" in select_sql

    updates = [s for s in statements if compiled(s).startswith("UPDATE")]
    assert len(updates) == 2
    expected = MockEmbeddings().embed_query(rows[0][1])
    first_vector = updates[0].compile(dialect=postgresql.dialect()).params["embedding"]
    assert list(first_vector) == expected
    assert len(first_vector) == EMBEDDING_DIMENSIONS
    session.commit.assert_awaited_once()


@pytest.mark.asyncio(loop_scope="function")
async def test_backfill_is_a_noop_when_nothing_is_missing():
    session = session_returning()

    assert await backfill_missing_embeddings(session) == 0
    session.commit.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_backfill_processes_multiple_batches():
    batch = [(uuid.uuid4(), f"chunk {i}") for i in range(2)]
    session = session_returning(batch, batch[:1])

    assert await backfill_missing_embeddings(session, batch_size=2) == 3
    assert session.commit.await_count == 2
