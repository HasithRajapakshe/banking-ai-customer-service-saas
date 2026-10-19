"""Tool permissions are enforced against the token's roles."""

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import settings
from app.core.internal_auth import require_internal_identity
from main import app
from tests.conftest import TEST_CARD_ID, TEST_CUSTOMER_ID, make_token

BASE = settings.banking_adapter_base_url.rstrip("/")


@pytest.fixture(autouse=True)
def real_token_check(identity_from_body):
    app.dependency_overrides.pop(require_internal_identity, None)


async def execute(tool: str, arguments: dict, roles: tuple) -> Response:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(
            "/api/v1/tools/execute",
            json={"tool_name": tool, "arguments": arguments},
            headers={"X-Internal-Token": make_token(roles=roles)},
        )


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_customer_can_use_customer_tools():
    route = respx.get(f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}/cards").mock(return_value=Response(200, json=[]))

    resp = await execute("card.list", {}, ("CUSTOMER",))

    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert route.call_count == 1


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize("roles", [("SUPPORT_AGENT",), ("ADMIN",), ()])
@respx.mock
async def test_role_without_permission_gets_403_and_adapter_is_never_called(roles, audit_records):
    route = respx.post(f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}/cards/{TEST_CARD_ID}/block").mock(
        return_value=Response(200, json={})
    )

    resp = await execute("card.block", {"card_id": str(TEST_CARD_ID)}, roles)

    body = resp.json()
    assert resp.status_code == 403
    assert body["error"]["code"] == "PERMISSION_DENIED"
    assert body["error"]["message"] == "Missing required permission: card.block"
    assert body["requires_confirmation"] is False  # denied before any challenge is issued
    assert route.call_count == 0
    assert [(r.status, r.authorization_result) for r in audit_records] == [("denied", "denied")]


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_support_agent_can_read_but_not_block():
    read = respx.get(f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}/cards").mock(return_value=Response(200, json=[]))

    assert (await execute("card.list", {}, ("SUPPORT_AGENT",))).status_code == 200
    assert (await execute("card.block", {"card_id": str(TEST_CARD_ID)}, ("SUPPORT_AGENT",))).status_code == 403
    assert read.call_count == 1
