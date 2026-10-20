"""Tenant isolation for the RAG API, using a mocked DB session.

The tenant comes from the internal identity token. Each test captures the SQL
the route sends and checks it is bound to the token's tenant.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects import postgresql

from app.core.database import get_db
from main import app
from tests.conftest import TENANT_A, auth


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
async def test_list_documents_requires_a_token(client, db_session):
    resp = await client.get("/api/v1/rag/documents")
    assert resp.status_code == 401
    db_session.execute.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_list_documents_filters_by_token_tenant(client, db_session):
    db_session.execute.return_value.scalars.return_value.all.return_value = []

    resp = await client.get("/api/v1/rag/documents", headers=auth())

    assert resp.status_code == 200
    assert resp.json() == []
    assert TENANT_A in bound_params(executed_statement(db_session)).values()


@pytest.mark.asyncio(loop_scope="function")
async def test_other_tenant_in_query_is_forbidden(client, db_session):
    resp = await client.get(f"/api/v1/rag/documents?tenant_id={uuid.uuid4()}", headers=auth())

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "IDENTITY_MISMATCH"
    db_session.execute.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_matching_tenant_in_query_is_accepted(client, db_session):
    db_session.execute.return_value.scalars.return_value.all.return_value = []
    resp = await client.get(f"/api/v1/rag/documents?tenant_id={TENANT_A}", headers=auth())
    assert resp.status_code == 200


@pytest.mark.asyncio(loop_scope="function")
async def test_get_document_is_scoped_to_token_tenant(client, db_session):
    document_id = uuid.uuid4()
    # The tenant-scoped query finds nothing (the document belongs to another tenant).
    db_session.execute.return_value.scalar_one_or_none.return_value = None

    resp = await client.get(f"/api/v1/rag/documents/{document_id}", headers=auth())

    assert resp.status_code == 404
    params = bound_params(executed_statement(db_session))
    assert TENANT_A in params.values()
    assert document_id in params.values()


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_document_from_other_tenant_returns_404(client, db_session):
    db_session.execute.return_value.scalar_one_or_none.return_value = None

    resp = await client.delete(f"/api/v1/rag/documents/{uuid.uuid4()}", headers=auth())

    assert resp.status_code == 404
    db_session.commit.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_search_filters_by_token_tenant(client, db_session):
    db_session.execute.return_value.all.return_value = []

    resp = await client.get("/api/v1/rag/search?query=card+fees", headers=auth())

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["results"] == []
    assert TENANT_A in bound_params(executed_statement(db_session)).values()


@pytest.mark.asyncio(loop_scope="function")
async def test_search_applies_similarity_threshold(client, db_session):
    db_session.execute.return_value.all.return_value = []

    resp = await client.get("/api/v1/rag/search?query=card+fees&similarity_threshold=0.4", headers=auth())

    assert resp.status_code == 200
    assert resp.json()["similarity_threshold"] == 0.4
    # The WHERE clause bounds cosine distance by 1 - threshold.
    params = bound_params(executed_statement(db_session))
    assert any(isinstance(v, float) and abs(v - 0.6) < 1e-9 for v in params.values())
