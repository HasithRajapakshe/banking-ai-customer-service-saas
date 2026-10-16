import pytest
from fakeredis import aioredis as fake_aioredis

from main import app


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    """Replace the shared Redis client with an in-memory fake.

    auth.py imports redis_client from rate_limit by name, so both module
    attributes must be patched.
    """
    client = fake_aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.core.rate_limit.redis_client", client)
    monkeypatch.setattr("app.api.routes.auth.redis_client", client)
    yield client


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()
