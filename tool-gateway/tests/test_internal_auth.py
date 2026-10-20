"""The real internal-token check (the body-derived test identity is removed)."""

import uuid

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import settings
from app.core.internal_auth import require_internal_identity
from main import app
from tests.conftest import TEST_CARD_ID, TEST_CUSTOMER_ID, TEST_TENANT_ID, TEST_USER_ID, make_execute_payload, make_token

BASE = settings.banking_adapter_base_url.rstrip("/")
OTHER_CUSTOMER = uuid.UUID("bbbbbbbb-0000-4000-8000-000000000002")


@pytest.fixture(autouse=True)
def real_token_check(identity_from_body):
    app.dependency_overrides.pop(require_internal_identity, None)


async def execute(payload: dict, token: str | None) -> Response:
    headers = {"X-Internal-Token": token} if token is not None else {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post("/api/v1/tools/execute", json=payload, headers=headers)


def card_details_payload(**identity) -> dict:
    return make_execute_payload("card.get_details", arguments={"card_id": str(TEST_CARD_ID)}, **identity)


def adapter_route():
    return respx.get(f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}/cards/{TEST_CARD_ID}").mock(
        return_value=Response(200, json={"id": str(TEST_CARD_ID), "card_last4": "6768"})
    )


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_valid_token_is_accepted_and_identity_comes_from_it():
    route = adapter_route()
    resp = await execute({"tool_name": "card.get_details", "arguments": {"card_id": str(TEST_CARD_ID)}}, make_token())

    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert route.call_count == 1  # customer path built from the token's customer_id


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize("token, code", [
    (None, "INTERNAL_TOKEN_REQUIRED"),
    ("not-a-jwt", "INTERNAL_TOKEN_INVALID"),
    ("EXPIRED", "INTERNAL_TOKEN_EXPIRED"),
    ("TAMPERED", "INTERNAL_TOKEN_INVALID"),
    ("WRONG_SECRET", "INTERNAL_TOKEN_INVALID"),
    ("WRONG_AUDIENCE", "INTERNAL_TOKEN_INVALID"),
    ("WRONG_ISSUER", "INTERNAL_TOKEN_INVALID"),
    ("NO_TENANT", "INTERNAL_TOKEN_INVALID"),
    ("SUB_MISMATCH", "INTERNAL_TOKEN_INVALID"),
])
@respx.mock
async def test_bad_tokens_are_rejected_before_any_tool_runs(token, code):
    route = adapter_route()
    if token == "EXPIRED":
        token = make_token(expires_in=-60)  # past the 5 s leeway
    elif token == "TAMPERED":
        header, body, signature = make_token().split(".")
        token = f"{header}.{body}.{signature[:-4]}AAAA"
    elif token == "WRONG_SECRET":
        token = make_token(secret="someone-elses-secret")
    elif token == "WRONG_AUDIENCE":
        token = make_token(aud="public")
    elif token == "WRONG_ISSUER":
        token = make_token(iss="attacker")
    elif token == "NO_TENANT":
        token = make_token(tenant_id=None)
    elif token == "SUB_MISMATCH":
        token = make_token(sub=str(uuid.uuid4()))

    resp = await execute(card_details_payload(), token)

    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == code
    assert route.call_count == 0


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize("field, value", [
    ("customer_id", OTHER_CUSTOMER),
    ("tenant_id", uuid.uuid4()),
    ("user_id", uuid.uuid4()),
])
@respx.mock
async def test_body_identity_that_disagrees_with_token_is_forbidden(field, value, audit_records):
    route = adapter_route()
    payload = card_details_payload(**{field: value})

    resp = await execute(payload, make_token())

    assert resp.status_code == 403
    assert resp.json()["detail"] == {
        "code": "IDENTITY_MISMATCH", "message": f"{field} does not match the authenticated identity.",
    }
    assert route.call_count == 0
    # The caller is authenticated, so the attempt is audited against the token's identity.
    (record,) = audit_records
    assert (record.status, record.error_code) == ("denied", "IDENTITY_MISMATCH")
    assert record.customer_id == TEST_CUSTOMER_ID and record.user_id == TEST_USER_ID


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_token_without_customer_cannot_run_banking_tools():
    route = adapter_route()
    admin_token = make_token(customer_id=None, roles=("ADMIN",))

    resp = await execute({"tool_name": "card.get_details", "arguments": {"card_id": str(TEST_CARD_ID)}}, admin_token)

    assert resp.status_code == 403
    assert route.call_count == 0


@pytest.mark.asyncio(loop_scope="function")
async def test_catalogue_stays_public_metadata():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/v1/tools")).status_code == 200


def test_ids_used_by_the_suite_are_consistent():
    assert TEST_TENANT_ID and TEST_USER_ID
