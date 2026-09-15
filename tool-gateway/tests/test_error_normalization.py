"""Tests for error normalization: timeout, connection, HTTP errors."""

import uuid

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from main import app
from tests.conftest import (
    TEST_ACCOUNT_ID,
    TEST_CUSTOMER_ID,
    make_execute_payload,
)

BASE = "http://127.0.0.1:8002"


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_timeout_normalized():
    """Banking Adapter timeout should be normalized."""
    import httpx

    respx.get(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/accounts/{TEST_ACCOUNT_ID}/balance"
    ).mock(side_effect=httpx.ReadTimeout("timeout"))

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "account.get_balance",
        arguments={"account_id": str(TEST_ACCOUNT_ID)},
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOOL_PROVIDER_TIMEOUT"
    assert data["executed"] is True


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_connection_error_normalized():
    """Banking Adapter connection error should be normalized."""
    import httpx

    respx.get(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/accounts/{TEST_ACCOUNT_ID}/balance"
    ).mock(side_effect=httpx.ConnectError("refused"))

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "account.get_balance",
        arguments={"account_id": str(TEST_ACCOUNT_ID)},
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOOL_PROVIDER_UNAVAILABLE"


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_404_normalized():
    """Banking Adapter 404 should be normalized."""
    respx.get(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/accounts/{TEST_ACCOUNT_ID}/balance"
    ).mock(
        return_value=Response(
            404,
            json={
                "detail": {
                    "code": "ACCOUNT_NOT_FOUND",
                    "message": "Account not found",
                }
            },
        )
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "account.get_balance",
        arguments={"account_id": str(TEST_ACCOUNT_ID)},
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "ACCOUNT_NOT_FOUND"
    assert data["executed"] is True


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_500_normalized():
    """Banking Adapter 500 should be normalized."""
    respx.get(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/accounts/{TEST_ACCOUNT_ID}/balance"
    ).mock(return_value=Response(500, json={}))

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "account.get_balance",
        arguments={"account_id": str(TEST_ACCOUNT_ID)},
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is False
    assert data["executed"] is True
    # Should not expose stack traces
    assert "traceback" not in str(data).lower()


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_mutation_not_retried():
    """Mutation requests must not be automatically retried."""
    call_count = 0

    def track_calls(request):
        nonlocal call_count
        call_count += 1
        return Response(
            503,
            json={
                "detail": {
                    "code": "PROVIDER_UNAVAILABLE",
                    "message": "Service unavailable",
                }
            },
        )

    respx.post(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/payments"
    ).mock(side_effect=track_calls)

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "payment.create",
        arguments={
            "source_account_id": str(TEST_ACCOUNT_ID),
            "beneficiary_id": str(uuid.uuid4()),
            "amount": "50.00",
            "currency": "USD",
        },
        confirmed=True,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        await client.post(
            "/api/v1/tools/execute", json=payload
        )

    # Should have been called exactly once (no retry)
    assert call_count == 1
