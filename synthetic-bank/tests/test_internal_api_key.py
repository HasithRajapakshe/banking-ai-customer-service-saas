"""Every banking route requires the X-Internal-API-Key header."""

import pytest

from tests.conftest import ACCOUNT_A_ID, CUSTOMER_A_ID, headers_for


@pytest.mark.asyncio(loop_scope="function")
async def test_missing_internal_api_key_is_rejected(client):
    resp = await client.get(
        f"/api/v1/accounts/{ACCOUNT_A_ID}",
        headers=headers_for(CUSTOMER_A_ID, api_key=None),
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INTERNAL_AUTH_REQUIRED"


@pytest.mark.asyncio(loop_scope="function")
async def test_wrong_internal_api_key_is_rejected(client):
    resp = await client.get(
        f"/api/v1/accounts/{ACCOUNT_A_ID}",
        headers=headers_for(CUSTOMER_A_ID, api_key="wrong-key"),
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_INTERNAL_API_KEY"


@pytest.mark.asyncio(loop_scope="function")
async def test_correct_internal_api_key_is_accepted(client):
    resp = await client.get(
        f"/api/v1/accounts/{ACCOUNT_A_ID}",
        headers=headers_for(CUSTOMER_A_ID),
    )
    assert resp.status_code == 200


@pytest.mark.asyncio(loop_scope="function")
async def test_health_does_not_require_internal_api_key(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
