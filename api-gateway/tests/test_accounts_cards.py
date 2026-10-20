"""/accounts and /cards go through the Tool Gateway, never the bank directly."""

import json
import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.api.dependencies import get_current_active_user
from app.core.config import settings
from app.models import AppUser
from app.services.tool_gateway_client import ToolGatewayClient
from main import app

USER = AppUser(
    id=uuid.UUID("11111111-1111-4111-8111-111111111111"),
    tenant_id=uuid.UUID("22222222-2222-4222-8222-222222222222"),
    customer_id=uuid.UUID("33333333-3333-4333-8333-333333333333"),
    email="alice@example.com",
    status="active",
)


@pytest.fixture
def client():
    async def user():
        return USER

    app.dependency_overrides[get_current_active_user] = user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_api_gateway_holds_no_banking_key():
    assert not hasattr(settings, "synthetic_bank_api_key")
    assert not hasattr(settings, "synthetic_bank_base_url")


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize("path, tool, args", [
    ("/api/v1/accounts", "account.list", {"limit": 100, "offset": 0}),
    ("/api/v1/cards", "card.list", {}),
    (f"/api/v1/accounts/{uuid.UUID(int=7)}", "account.get_details", {"account_id": str(uuid.UUID(int=7))}),
    (f"/api/v1/accounts/{uuid.UUID(int=7)}/transactions?limit=5",
     "account.get_transactions", {"account_id": str(uuid.UUID(int=7)), "limit": 5, "offset": 0}),
])
async def test_routes_use_tool_gateway_with_a_signed_token(client, path, tool, args):
    with patch("app.services.tool_gateway_client.tool_gateway_client.run", new=AsyncMock(return_value=[{"id": "x"}])) as run:
        resp = await client.get(path)

    assert resp.status_code == 200
    assert resp.json() == [{"id": "x"}]
    called_tool, called_args = run.await_args.args
    assert (called_tool, called_args) == (tool, args)
    claims = jwt.decode(run.await_args.kwargs["token"], settings.internal_jwt_secret, algorithms=["HS256"],
                        audience=settings.internal_jwt_audience)
    assert claims["customer_id"] == str(USER.customer_id)
    assert claims["roles"] == ["CUSTOMER"]


def gateway(handler) -> ToolGatewayClient:
    return ToolGatewayClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio(loop_scope="function")
async def test_client_returns_tool_data_and_sends_the_token():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["token"] = request.headers["X-Internal-Token"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"success": True, "data": [{"card_last4": "6768"}]})

    data = await gateway(handler).run("card.list", {}, token="tok", correlation_id="c")

    assert data == [{"card_last4": "6768"}]
    assert seen == {"token": "tok", "body": {"tool_name": "card.list", "arguments": {}}}


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize("status, body, expected", [
    (200, {"success": False, "error": {"code": "NOT_FOUND", "message": "Account not found"}}, 404),
    (200, {"success": False, "error": {"code": "INVALID_TOOL_ARGUMENTS", "message": "bad"}}, 422),
    (403, {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Missing required permission"}}, 403),
    (401, {"detail": {"code": "INTERNAL_TOKEN_EXPIRED", "message": "expired"}}, 403),
    (200, {"success": False, "error": {"code": "TOOL_PROVIDER_UNAVAILABLE", "message": "down"}}, 502),
    (500, {}, 502),
])
async def test_client_maps_gateway_errors(status, body, expected):
    with pytest.raises(HTTPException) as raised:
        await gateway(lambda request: httpx.Response(status, json=body)).run("account.list", {}, token="t", correlation_id="c")
    assert raised.value.status_code == expected


@pytest.mark.asyncio(loop_scope="function")
async def test_unreachable_gateway_is_503():
    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(HTTPException) as raised:
        await gateway(handler).run("account.list", {}, token="t", correlation_id="c")
    assert raised.value.status_code == 503
