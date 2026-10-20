"""The agent forwards the API Gateway's internal token unchanged."""

import uuid

import pytest
import pytest_asyncio
import respx
from httpx import ASGITransport, AsyncClient, Response

from app.clients.rag_client import rag_client
from app.clients.tool_gateway_client import tool_gateway_client
from app.core.config import settings
from app.core.internal_token import current_internal_token
from main import app

TG = settings.tool_gateway_base_url.rstrip("/")
RAG = settings.rag_base_url.rstrip("/")


def chat_body(message: str) -> dict:
    return {
        "message": message, "tenant_id": str(uuid.uuid4()), "customer_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()), "conversation_id": str(uuid.uuid4()),
    }


@pytest_asyncio.fixture(autouse=True)
async def fresh_clients():
    # Module-level clients bind to an event loop; recreate them per test.
    await tool_gateway_client.close()
    await rag_client.close()
    yield
    await tool_gateway_client.close()
    await rag_client.close()


async def post_chat(message: str, token: str | None):
    headers = {"X-Internal-Token": token} if token else {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post("/api/v1/agent/chat", json=chat_body(message), headers=headers)


@pytest.mark.asyncio
@respx.mock
async def test_token_is_forwarded_to_tool_gateway():
    route = respx.post(f"{TG}/api/v1/tools/execute").mock(return_value=Response(200, json={
        "success": True, "tool_name": "account.list", "risk_level": "LOW", "data": [],
        "error": None, "correlation_id": "c", "requires_confirmation": False, "executed": True,
    }))

    resp = await post_chat("show my accounts", "signed-token-123")

    assert resp.status_code == 200
    assert route.calls.last.request.headers["X-Internal-Token"] == "signed-token-123"


@pytest.mark.asyncio
@respx.mock
async def test_token_is_forwarded_to_rag():
    route = respx.get(f"{RAG}/api/v1/rag/search").mock(return_value=Response(200, json={"success": True, "results": []}))

    await post_chat("what is the policy for a lost card?", "signed-token-456")

    assert route.calls.last.request.headers["X-Internal-Token"] == "signed-token-456"


@pytest.mark.asyncio
@respx.mock
async def test_token_does_not_leak_into_the_next_request():
    route = respx.post(f"{TG}/api/v1/tools/execute").mock(return_value=Response(401, json={
        "detail": {"code": "INTERNAL_TOKEN_REQUIRED", "message": "Internal identity token is required."}}))

    await post_chat("show my accounts", "first-token")
    await post_chat("show my accounts", None)

    assert route.calls[0].request.headers["X-Internal-Token"] == "first-token"
    assert "X-Internal-Token" not in route.calls[1].request.headers
    assert current_internal_token.get() is None


@pytest.mark.asyncio
@respx.mock
async def test_gateway_refusal_becomes_a_safe_failed_reply():
    respx.post(f"{TG}/api/v1/tools/execute").mock(return_value=Response(403, json={
        "success": False, "tool_name": "card.block", "risk_level": "HIGH", "data": None,
        "error": {"code": "PERMISSION_DENIED", "message": "Missing required permission: card.block"},
        "correlation_id": "c", "requires_confirmation": False, "executed": False,
    }))

    resp = await post_chat(f"block card {uuid.uuid4()}", "token")

    body = resp.json()
    assert resp.status_code == 200
    assert body["status"] == "failed"
    assert body["tool_executed"] is False
    assert "Missing required permission" in body["message"]


@pytest.mark.asyncio
@respx.mock
async def test_unauthenticated_refusal_is_normalised():
    respx.post(f"{TG}/api/v1/tools/execute").mock(return_value=Response(401, json={
        "detail": {"code": "INTERNAL_TOKEN_EXPIRED", "message": "Internal identity token has expired."}}))

    result = await tool_gateway_client.execute(
        tool_name="account.list", tenant_id="t", customer_id="c", user_id="u", conversation_id="v",
        channel="web", arguments={}, confirmed=False, correlation_id="corr",
    )

    assert result["success"] is False
    assert result["executed"] is False
    assert result["error"]["code"] == "INTERNAL_TOKEN_EXPIRED"
