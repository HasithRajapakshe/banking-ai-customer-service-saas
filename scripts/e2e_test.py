"""End-to-end test against the running Compose stack.

    docker compose up -d --build
    pip install -r scripts/requirements-e2e.txt
    python -m pytest scripts/e2e_test.py -v

Every check goes through the public API Gateway, so banking actions travel the
real path: API Gateway -> AI Agent -> Tool Gateway -> Banking Adapter ->
Synthetic Bank.

Test setup only: no public API lists a customer's cards, so the card under
test is looked up directly in the demo database. Blocking it changes demo
data, so the fixture restores the card to "active" afterwards (and before the
test, if an earlier run was interrupted).
"""

import os
import uuid

import httpx
import psycopg
import pytest

API_URL = os.environ.get("E2E_API_URL", "http://localhost:8001/api/v1")
DATABASE_URL = os.environ.get(
    "E2E_DATABASE_URL",
    "postgresql://banking_app:change_me_in_production@localhost:5432/banking_ai",
)
PASSWORD = "password123"


# =========================
# Helpers
# =========================


class User:
    def __init__(self, client: httpx.Client, email: str):
        resp = client.post(f"{API_URL}/auth/login", json={"username": email, "password": PASSWORD})
        assert resp.status_code == 200, f"login {email}: {resp.status_code} {resp.text}"
        self.client = client
        self.email = email
        self.headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        me = client.get(f"{API_URL}/auth/me", headers=self.headers)
        assert me.status_code == 200, me.text
        self.customer_id = me.json()["customer_id"]

    def get(self, path: str) -> httpx.Response:
        return self.client.get(f"{API_URL}{path}", headers=self.headers)

    def chat(self, conversation_id: str, message: str, challenge_code: str | None = None) -> httpx.Response:
        body = {"message": message, "conversation_id": conversation_id}
        if challenge_code is not None:
            body["challenge_code"] = challenge_code
        return self.client.post(f"{API_URL}/chat", json=body, headers=self.headers)


def ok_json(resp: httpx.Response) -> dict:
    assert resp.status_code == 200, f"{resp.request.method} {resp.request.url}: {resp.status_code} {resp.text}"
    return resp.json()


# =========================
# Fixtures
# =========================


@pytest.fixture(scope="module")
def client():
    with httpx.Client(timeout=60) as c:
        yield c


@pytest.fixture(scope="module")
def alice(client) -> User:
    return User(client, "alice@example.com")


@pytest.fixture(scope="module")
def bob(client) -> User:
    return User(client, "bob@example.com")


@pytest.fixture
def alice_card(alice):
    """Alice's card as (id, last4); active for the test, restored afterwards."""
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        row = conn.execute(
            "SELECT id, card_last4 FROM card WHERE customer_id = %s ORDER BY card_last4 LIMIT 1",
            (alice.customer_id,),
        ).fetchone()
        assert row is not None, "alice has no card in the demo data"
        card_id, last4 = str(row[0]), row[1]
        conn.execute("UPDATE card SET status = 'active', blocked_at = NULL WHERE id = %s", (card_id,))

    yield card_id, last4

    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        conn.execute("UPDATE card SET status = 'active', blocked_at = NULL WHERE id = %s", (card_id,))


def card_status_via_agent(user: User, card_id: str) -> str:
    """Read the card through the full chain (card.get_details tool)."""
    body = ok_json(user.chat(str(uuid.uuid4()), f"Show card details {card_id}"))
    assert body["tool_name"] == "card.get_details", body
    assert body["tool_executed"] is True, body
    return body["data"]["status"]


# =========================
# Tests
# =========================


def test_alice_lists_accounts(alice):
    accounts = ok_json(alice.get("/accounts"))
    assert len(accounts) >= 1
    assert all(account["customer_id"] == alice.customer_id for account in accounts)


def test_policy_question_is_answered_from_knowledge_base(alice):
    body = ok_json(alice.chat(str(uuid.uuid4()), "What is the policy for a lost or stolen card?"))

    assert body["status"] == "completed", body
    assert body["intent"] == "knowledge_question"
    assert "Lost or Stolen Card" in body["message"], body["message"]


def test_block_card_requires_confirmation_and_completes(alice, bob, alice_card):
    card_id, last4 = alice_card
    conversation_id = str(uuid.uuid4())

    # 1. The request is held for confirmation; nothing is executed yet.
    pending = ok_json(alice.chat(conversation_id, f"Block my card {card_id}"))
    assert pending["status"] == "confirmation_required", pending
    assert pending["requires_confirmation"] is True
    assert pending["tool_executed"] is False
    assert pending["action_summary"] == f"Block card ending {last4}"
    challenge = pending["confirmation_challenge"]
    assert challenge
    assert "tool_arguments" not in pending
    assert card_status_via_agent(alice, card_id) == "active"

    # 2. Bob cannot use Alice's challenge: not in her conversation, not in his own.
    assert bob.chat(conversation_id, "Confirm", challenge).status_code == 403
    assert bob.chat(str(uuid.uuid4()), "Confirm", challenge).status_code == 409
    assert card_status_via_agent(alice, card_id) == "active"

    # 3. Alice confirms: the stored action is executed.
    done = ok_json(alice.chat(conversation_id, "Confirm", challenge))
    assert done["status"] == "completed", done
    assert done["tool_executed"] is True
    assert done["message"] == f"Your card ending {last4} has been blocked."
    assert card_status_via_agent(alice, card_id) == "blocked"

    # 4. Replaying the same challenge fails and changes nothing.
    replay = alice.chat(conversation_id, "Confirm", challenge)
    assert replay.status_code == 409, replay.text


def test_block_my_card_without_an_id_resolves_the_card(alice, alice_card):
    """Natural language, no UUID: the agent finds Alice's card itself (card.list)."""
    card_id, last4 = alice_card
    conversation_id = str(uuid.uuid4())

    body = ok_json(alice.chat(conversation_id, "I lost my card, please block my card"))

    if body["status"] == "needs_clarification":
        # Acceptable only if it asks about Alice's own card.
        assert last4 in body["message"], body
        return
    assert body["status"] == "confirmation_required", body
    assert body["action_summary"] == f"Block card ending {last4}"
    assert card_id not in body["message"]  # the resolved ID is never shown
    assert card_status_via_agent(alice, card_id) == "active"

    done = ok_json(alice.chat(conversation_id, "Confirm", body["confirmation_challenge"]))
    assert done["tool_executed"] is True
    assert card_status_via_agent(alice, card_id) == "blocked"


def test_client_cannot_pick_a_tool_or_self_confirm(alice, alice_card):
    card_id, _ = alice_card
    resp = alice.client.post(
        f"{API_URL}/chat",
        json={
            "message": "hi",
            "conversation_id": str(uuid.uuid4()),
            "tool_name": "card.block",
            "tool_arguments": {"card_id": card_id},
            "confirmed": True,
        },
        headers=alice.headers,
    )
    assert resp.status_code == 422
    assert card_status_via_agent(alice, card_id) == "active"
