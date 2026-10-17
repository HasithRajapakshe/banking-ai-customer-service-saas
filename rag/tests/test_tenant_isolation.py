"""Tenant isolation tests for the RAG API using a mocked DB session.

Each test captures the SQL statement the route sends to the session and checks
that it is scoped to the caller's tenant_id.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects import postgresql

from app.core.database import get_db
from main import app


def bound_params(stmt) -> dict:
    return stmt.compile(dialect=postgresql.dialect()).params


@pytest.fixture
def db_session():
    session = AsyncMock()
    # execute() is awaited; the result object it returns is synchronous.
    session.execute.return_value = MagicMock()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def executed_statement(db_session):
    db_session.execute.assert_awaited_once()
    return db_session.execute.await_args.args[0]


@pytest.mark.asyncio(loop_scope="function")
async def test_list_documents_requires_tenant_id(client, db_session):
    resp = await client.get("/api/v1/rag/documents")
    assert resp.status_code == 422
    db_session.execute.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_list_documents_filters_by_tenant(client, db_session):
    tenant_a = uuid.uuid4()
    db_session.execute.return_value.scalars.return_value.all.return_value = []

    resp = await client.get(f"/api/v1/rag/documents?tenant_id={tenant_a}")

    assert resp.status_code == 200
    assert resp.json() == []
    params = bound_params(executed_statement(db_session))
    assert tenant_a in params.values()


@pytest.mark.asyncio(loop_scope="function")
async def test_get_document_from_other_tenant_returns_404(client, db_session):
    tenant_b = uuid.uuid4()
    document_id = uuid.uuid4()
    # The tenant-scoped query finds nothing for tenant B.
    db_session.execute.return_value.scalar_one_or_none.return_value = None

    resp = await client.get(f"/api/v1/rag/documents/{document_id}?tenant_id={tenant_b}")

    assert resp.status_code == 404
    params = bound_params(executed_statement(db_session))
    assert tenant_b in params.values()
    assert document_id in params.values()


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_document_from_other_tenant_returns_404(client, db_session):
    tenant_b = uuid.uuid4()
    db_session.execute.return_value.scalar_one_or_none.return_value = None

    resp = await client.delete(f"/api/v1/rag/documents/{uuid.uuid4()}?tenant_id={tenant_b}")

    assert resp.status_code == 404
    db_session.commit.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_search_filters_by_tenant(client, db_session):
    tenant_a = uuid.uuid4()
    db_session.execute.return_value.all.return_value = []

    resp = await client.get(f"/api/v1/rag/search?query=card+fees&tenant_id={tenant_a}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["results"] == []
    params = bound_params(executed_statement(db_session))
    assert tenant_a in params.values()


@pytest.mark.asyncio(loop_scope="function")
async def test_search_applies_similarity_threshold(client, db_session):
    db_session.execute.return_value.all.return_value = []

    resp = await client.get(
        f"/api/v1/rag/search?query=card+fees&tenant_id={uuid.uuid4()}&similarity_threshold=0.4"
    )

    assert resp.status_code == 200
    assert resp.json()["similarity_threshold"] == 0.4
    # The WHERE clause bounds cosine distance by 1 - threshold.
    params = bound_params(executed_statement(db_session))
    assert any(isinstance(v, float) and abs(v - 0.6) < 1e-9 for v in params.values())
