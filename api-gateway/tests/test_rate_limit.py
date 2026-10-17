import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core import rate_limit
from app.core.security import create_access_token
from main import app

LIMIT = 3


@pytest.fixture(autouse=True)
def small_limit(monkeypatch):
    monkeypatch.setattr(rate_limit, "RATE_LIMIT_REQUESTS", LIMIT)


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def bearer(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': user_id})}"}


@pytest.mark.asyncio(loop_scope="function")
async def test_exceeding_limit_returns_429_json(client):
    headers = bearer(str(uuid.uuid4()))
    for _ in range(LIMIT):
        assert (await client.get("/health", headers=headers)).status_code == 200

    resp = await client.get("/health", headers=headers)

    assert resp.status_code == 429
    assert resp.headers["Retry-After"] == str(rate_limit.RATE_LIMIT_WINDOW)
    assert resp.json()["error"]["code"] == "RATE_LIMITED"


@pytest.mark.asyncio(loop_scope="function")
async def test_users_have_separate_buckets(client):
    alice, bob = bearer(str(uuid.uuid4())), bearer(str(uuid.uuid4()))
    # HS256 tokens share their first characters (the encoded header), which is
    # what the old 10-character key used.
    assert alice["Authorization"][:17] == bob["Authorization"][:17]

    for _ in range(LIMIT):
        assert (await client.get("/health", headers=alice)).status_code == 200
    assert (await client.get("/health", headers=alice)).status_code == 429

    assert (await client.get("/health", headers=bob)).status_code == 200


@pytest.mark.asyncio(loop_scope="function")
async def test_every_request_is_recorded(client, fake_redis):
    user_id = str(uuid.uuid4())
    headers = bearer(user_id)
    for _ in range(LIMIT):
        await client.get("/health", headers=headers)

    # Same-second requests must not overwrite each other in the window.
    assert await fake_redis.zcard(f"rate_limit:user:{user_id}") == LIMIT


@pytest.mark.asyncio(loop_scope="function")
async def test_invalid_token_falls_back_to_ip_bucket(client, fake_redis):
    await client.get("/health", headers={"Authorization": "Bearer not-a-jwt"})
    keys = await fake_redis.keys("rate_limit:*")
    assert keys == ["rate_limit:ip:127.0.0.1"]
