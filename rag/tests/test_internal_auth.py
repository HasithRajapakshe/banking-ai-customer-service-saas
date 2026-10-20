import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from main import app
from tests.conftest import make_token


@pytest.fixture
def db_session():
    session = AsyncMock()
    session.execute.return_value = MagicMock()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.clear()


async def search(headers: dict):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get("/api/v1/rag/search?query=lost+card", headers=headers)


def tampered() -> str:
    header, body, signature = make_token().split(".")
    return f"{header}.{body}.{signature[:-4]}AAAA"


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize("headers, code", [
    ({}, "INTERNAL_TOKEN_REQUIRED"),
    ({"X-Internal-Token": "garbage"}, "INTERNAL_TOKEN_INVALID"),
    ({"X-Internal-Token": make_token(expires_in=-60)}, "INTERNAL_TOKEN_EXPIRED"),
    ({"X-Internal-Token": tampered()}, "INTERNAL_TOKEN_INVALID"),
    ({"X-Internal-Token": make_token(secret="not-the-secret")}, "INTERNAL_TOKEN_INVALID"),
    ({"X-Internal-Token": make_token(aud="public")}, "INTERNAL_TOKEN_INVALID"),
    ({"X-Internal-Token": make_token(tenant_id=None)}, "INTERNAL_TOKEN_INVALID"),
    ({"X-Internal-Token": make_token(sub=str(uuid.uuid4()))}, "INTERNAL_TOKEN_INVALID"),
])
async def test_bad_tokens_are_rejected_without_touching_the_database(db_session, headers, code):
    resp = await search(headers)
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == code
    db_session.execute.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_valid_token_is_accepted(db_session):
    db_session.execute.return_value.all.return_value = []
    resp = await search({"X-Internal-Token": make_token()})
    assert resp.status_code == 200


@pytest.mark.asyncio(loop_scope="function")
async def test_health_needs_no_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/health")).status_code == 200
