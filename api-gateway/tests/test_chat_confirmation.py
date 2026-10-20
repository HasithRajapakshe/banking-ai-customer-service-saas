"""Confirmation flow through the public chat endpoint.

The AI Agent call is mocked; Redis is the in-memory fake from conftest.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_active_user, get_db
from app.models import AppUser, Conversation
from app.services.pending_action_service import pending_action_service
from main import app

TENANT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
ALICE = AppUser(
    id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    tenant_id=TENANT_ID,
    customer_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
    email="alice@example.com",
    status="active",
)
BOB = AppUser(
    id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
    tenant_id=TENANT_ID,
    customer_id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
    email="bob@example.com",
    status="active",
)
CARD_ID = "aa4151ec-1de5-4302-a129-a43e81acc788"

CONFIRMATION_RESPONSE = {
    "conversation_id": None,
    "correlation_id": "c",
    "status": "confirmation_required",
    "message": "Please confirm: Block card ending 6768.",
    "intent": "block_card",
    "tool_name": "card.block",
    "tool_executed": False,
    "requires_confirmation": True,
    "confirmation_challenge": "ABCD1234",
    "action_summary": "Block card ending 6768",
    "tool_arguments": {"card_id": CARD_ID},
    "data": None,
}
EXECUTED_RESPONSE = {
    **CONFIRMATION_RESPONSE,
    "status": "completed",
    "message": "Your card ending 6768 has been blocked.",
    "tool_executed": True,
    "requires_confirmation": False,
    "confirmation_challenge": None,
    "action_summary": None,
    "tool_arguments": None,
    "data": {"id": CARD_ID, "status": "blocked"},
}


def agent_reply(body: dict) -> dict:
    return dict(body)


class Session:
    """Minimal DB double: conversations owned by whoever created them."""

    def __init__(self):
        self.conversations: dict[uuid.UUID, Conversation] = {}
        self.add = MagicMock(side_effect=self._add)
        self.commit = AsyncMock()

    def _add(self, obj):
        if isinstance(obj, Conversation):
            self.conversations[obj.id] = obj

    async def execute(self, stmt):
        conversation_id = next(
            p.value for p in stmt.compile().binds.values() if isinstance(p.value, uuid.UUID)
        )
        result = MagicMock()
        result.scalar_one_or_none.return_value = self.conversations.get(conversation_id)
        return result


@pytest.fixture
def db():
    session = Session()
    app.dependency_overrides[get_db] = lambda: session
    return session


def as_user(user: AppUser) -> None:
    async def override():
        return user

    app.dependency_overrides[get_current_active_user] = override


@pytest.fixture
def client(db):
    as_user(ALICE)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def agent():
    with patch("app.api.routes.chat.ai_agent_client.chat", new_callable=AsyncMock) as post:
        yield post


async def request_block(client, agent, conversation_id) -> dict:
    agent.return_value = agent_reply(CONFIRMATION_RESPONSE)
    resp = await client.post(
        "/api/v1/chat",
        json={"message": f"Block my card {CARD_ID}", "conversation_id": str(conversation_id)},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize(
    "field", [{"tool_name": "card.block"}, {"tool_arguments": {"card_id": CARD_ID}}, {"confirmed": True}]
)
async def test_client_cannot_choose_tool_or_confirm(client, agent, field):
    resp = await client.post(
        "/api/v1/chat", json={"message": "hi", "conversation_id": str(uuid.uuid4()), **field}
    )
    assert resp.status_code == 422
    agent.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_challenge_is_stored_server_side(client, agent):
    conversation_id = uuid.uuid4()
    body = await request_block(client, agent, conversation_id)

    assert body["requires_confirmation"] is True
    assert body["confirmation_challenge"] == "ABCD1234"
    assert body["action_summary"] == "Block card ending 6768"
    assert "tool_arguments" not in body

    stored = await pending_action_service.get(conversation_id)
    assert stored.tool_name == "card.block"
    assert stored.tool_arguments == {"card_id": CARD_ID}
    assert stored.user_id == ALICE.id


@pytest.mark.asyncio(loop_scope="function")
async def test_confirm_replays_stored_action(client, agent):
    conversation_id = uuid.uuid4()
    await request_block(client, agent, conversation_id)

    agent.return_value = agent_reply(EXECUTED_RESPONSE)
    resp = await client.post(
        "/api/v1/chat",
        json={"message": "Confirm", "conversation_id": str(conversation_id), "challenge_code": "ABCD1234"},
    )

    assert resp.status_code == 200
    assert resp.json()["tool_executed"] is True
    sent = agent.await_args.args[0]
    assert sent["tool_name"] == "card.block"
    assert sent["tool_arguments"] == {"card_id": CARD_ID}
    assert sent["confirmed"] is True
    assert sent["challenge_code"] == "ABCD1234"
    assert sent["user_id"] == str(ALICE.id)
    assert await pending_action_service.get(conversation_id) is None


@pytest.mark.asyncio(loop_scope="function")
async def test_replayed_challenge_is_rejected(client, agent):
    conversation_id = uuid.uuid4()
    await request_block(client, agent, conversation_id)
    confirm = {"message": "Confirm", "conversation_id": str(conversation_id), "challenge_code": "ABCD1234"}

    agent.return_value = agent_reply(EXECUTED_RESPONSE)
    assert (await client.post("/api/v1/chat", json=confirm)).status_code == 200
    calls = agent.await_count

    assert (await client.post("/api/v1/chat", json=confirm)).status_code == 409
    assert agent.await_count == calls  # the agent was not called again


@pytest.mark.asyncio(loop_scope="function")
async def test_wrong_code_is_rejected_and_keeps_pending_action(client, agent):
    conversation_id = uuid.uuid4()
    await request_block(client, agent, conversation_id)
    calls = agent.await_count

    resp = await client.post(
        "/api/v1/chat",
        json={"message": "Confirm", "conversation_id": str(conversation_id), "challenge_code": "WRONG000"},
    )

    assert resp.status_code == 409
    assert agent.await_count == calls
    assert (await pending_action_service.get(conversation_id)).challenge_code == "ABCD1234"


@pytest.mark.asyncio(loop_scope="function")
async def test_other_user_cannot_use_challenge(client, agent):
    alice_conversation = uuid.uuid4()
    await request_block(client, agent, alice_conversation)
    calls = agent.await_count

    as_user(BOB)
    # In Alice's conversation: not his conversation.
    in_alice_conv = await client.post(
        "/api/v1/chat",
        json={"message": "Confirm", "conversation_id": str(alice_conversation), "challenge_code": "ABCD1234"},
    )
    # In his own conversation: nothing pending there.
    in_own_conv = await client.post(
        "/api/v1/chat",
        json={"message": "Confirm", "conversation_id": str(uuid.uuid4()), "challenge_code": "ABCD1234"},
    )

    assert in_alice_conv.status_code == 403
    assert in_own_conv.status_code == 409
    assert agent.await_count == calls
    assert (await pending_action_service.get(alice_conversation)) is not None


@pytest.mark.asyncio(loop_scope="function")
async def test_cancel_discards_the_pending_action(client, agent):
    conversation_id = uuid.uuid4()
    await request_block(client, agent, conversation_id)

    resp = await client.delete(f"/api/v1/chat/conversations/{conversation_id}/pending-action")

    assert resp.status_code == 204
    assert await pending_action_service.get(conversation_id) is None
    confirm = await client.post(
        "/api/v1/chat",
        json={"message": "Confirm", "conversation_id": str(conversation_id), "challenge_code": "ABCD1234"},
    )
    assert confirm.status_code == 409


@pytest.mark.asyncio(loop_scope="function")
async def test_other_user_cannot_cancel_someone_elses_pending_action(client, agent):
    conversation_id = uuid.uuid4()
    await request_block(client, agent, conversation_id)

    as_user(BOB)
    resp = await client.delete(f"/api/v1/chat/conversations/{conversation_id}/pending-action")

    assert resp.status_code == 204  # reveals nothing
    assert await pending_action_service.get(conversation_id) is not None
