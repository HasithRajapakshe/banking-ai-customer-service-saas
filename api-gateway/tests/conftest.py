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
def customer_roles():
    """Routes that sign internal tokens look up the user's roles (a DB query);
    default every test user to CUSTOMER. Tests may override this."""
    from app.api.dependencies import get_current_user_roles
    from app.models import Role

    async def roles():
        return [Role(role_code="CUSTOMER", role_name="Customer", tenant_id=None)]

    app.dependency_overrides[get_current_user_roles] = roles


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()
