import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app

CARD_ID = "aa4151ec-1de5-4302-a129-a43e81acc788"


def chat_payload(conversation_id: str, message: str, **extra) -> dict:
    return {
        "message": message,
        "tenant_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        **extra,
    }


def gateway_result(tool_name: str, **fields) -> dict:
    return {
        "success": False,
        "tool_name": tool_name,
        "risk_level": "HIGH",
        "data": None,
        "error": None,
        "correlation_id": "c",
        "requires_confirmation": False,
        "confirmation_challenge": None,
        "executed": False,
        **fields,
    }


def fake_gateway(*, block_result: dict):
    """Tool Gateway double: card.get_details succeeds, card.block returns block_result."""

    async def execute(**kwargs):
        if kwargs["tool_name"] == "card.get_details":
            return gateway_result(
                "card.get_details", success=True, executed=True,
                risk_level="LOW", data={"id": CARD_ID, "card_last4": "6768"},
            )
        return block_result

    return AsyncMock(side_effect=execute)


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_high_risk_request_returns_challenge_and_summary(client):
    mock = fake_gateway(block_result=gateway_result(
        "card.block",
        error={"code": "CONFIRMATION_REQUIRED", "message": "Explicit confirmation is required."},
        requires_confirmation=True,
        confirmation_challenge="ABCD1234",
    ))
    with patch("app.graph.workflow.tool_gateway_client.execute", new=mock), \
         patch("app.services.action_summary.tool_gateway_client.execute", new=mock):
        resp = await client.post(
            "/api/v1/agent/chat",
            json=chat_payload(str(uuid.uuid4()), f"Block my card {CARD_ID}"),
        )

    body = resp.json()
    assert resp.status_code == 200
    assert body["status"] == "confirmation_required"
    assert body["requires_confirmation"] is True
    assert body["confirmation_challenge"] == "ABCD1234"
    assert body["action_summary"] == "Block card ending 6768"
    assert body["tool_name"] == "card.block"
    assert body["tool_arguments"] == {"card_id": CARD_ID}
    assert body["tool_executed"] is False


@pytest.mark.asyncio
async def test_confirmation_passes_challenge_code_to_tool_gateway(client):
    mock = fake_gateway(block_result=gateway_result(
        "card.block", success=True, executed=True,
        data={"id": CARD_ID, "card_last4": "6768", "status": "blocked"},
    ))
    with patch("app.graph.workflow.tool_gateway_client.execute", new=mock):
        resp = await client.post(
            "/api/v1/agent/chat",
            json=chat_payload(
                str(uuid.uuid4()), "Confirm",
                confirmed=True, challenge_code="ABCD1234",
                tool_name="card.block", tool_arguments={"card_id": CARD_ID},
            ),
        )

    body = resp.json()
    assert body["status"] == "completed"
    assert body["tool_executed"] is True
    assert body["message"] == "Your card ending 6768 has been blocked."
    assert body["confirmation_challenge"] is None

    sent = mock.await_args.kwargs
    assert sent["tool_name"] == "card.block"
    assert sent["confirmed"] is True
    assert sent["challenge_code"] == "ABCD1234"


@pytest.mark.asyncio
async def test_challenge_does_not_leak_into_next_turn(client):
    conversation_id = str(uuid.uuid4())
    mock = fake_gateway(block_result=gateway_result(
        "card.block",
        error={"code": "CONFIRMATION_REQUIRED", "message": "Explicit confirmation is required."},
        requires_confirmation=True,
        confirmation_challenge="ABCD1234",
    ))
    with patch("app.graph.workflow.tool_gateway_client.execute", new=mock), \
         patch("app.services.action_summary.tool_gateway_client.execute", new=mock):
        first = await client.post(
            "/api/v1/agent/chat", json=chat_payload(conversation_id, f"Block my card {CARD_ID}")
        )
        second = await client.post(
            "/api/v1/agent/chat", json=chat_payload(conversation_id, "hello")
        )

    assert first.json()["confirmation_challenge"] == "ABCD1234"
    body = second.json()
    assert body["requires_confirmation"] is False
    assert body["confirmation_challenge"] is None
    assert body["action_summary"] is None
    assert body["tool_name"] is None
    assert body["data"] is None


@pytest.mark.asyncio
async def test_unknown_request_fields_are_still_rejected(client):
    resp = await client.post(
        "/api/v1/agent/chat",
        json=chat_payload(str(uuid.uuid4()), "hello", challenge_code="ABCD1234", is_admin=True),
    )
    assert resp.status_code == 422
