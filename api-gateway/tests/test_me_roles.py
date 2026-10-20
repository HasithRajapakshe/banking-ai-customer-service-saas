import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user_roles
from app.models import Role
from main import app


@pytest.mark.asyncio(loop_scope="function")
async def test_me_roles_returns_role_codes():
    async def roles_override():
        return [
            Role(id=uuid.uuid4(), tenant_id=None, role_code="ADMIN", role_name="Administrator"),
            Role(id=uuid.uuid4(), tenant_id=None, role_code="CUSTOMER", role_name="Customer"),
        ]

    app.dependency_overrides[get_current_user_roles] = roles_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me/roles")

    assert resp.status_code == 200
    assert resp.json() == ["ADMIN", "CUSTOMER"]
