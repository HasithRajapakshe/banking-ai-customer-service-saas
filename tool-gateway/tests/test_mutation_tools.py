"""Tests for mutation tools: confirmation gate, execution."""

import uuid

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from main import app
from tests.conftest import (
    TEST_ACCOUNT_ID,
    TEST_BENEFICIARY_ID,
    TEST_CARD_ID,
    TEST_COMPLAINT_ID,
    TEST_CUSTOMER_ID,
    TEST_PAYMENT_ID,
    TEST_TENANT_ID,
    make_execute_payload,
)

BASE = "http://127.0.0.1:8002"


# =========================
# Confirmation Gate: HIGH risk
# =========================


@pytest.mark.asyncio(loop_scope="function")
async def test_high_risk_unconfirmed_blocked():
    """HIGH-risk tool must NOT execute without confirmation."""
    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "card.block",
        arguments={"card_id": str(TEST_CARD_ID)},
        confirmed=False,
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
    assert data["error"]["code"] == "CONFIRMATION_REQUIRED"
    assert data["requires_confirmation"] is True
    assert data["executed"] is False
    assert data["risk_level"] == "HIGH"


@pytest.mark.asyncio(loop_scope="function")
async def test_critical_risk_unconfirmed_blocked():
    """CRITICAL-risk tool must NOT execute without confirmation."""
    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "payment.create",
        arguments={
            "source_account_id": str(TEST_ACCOUNT_ID),
            "beneficiary_id": str(TEST_BENEFICIARY_ID),
            "amount": "100.00",
            "currency": "USD",
        },
        confirmed=False,
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
    assert data["error"]["code"] == "CONFIRMATION_REQUIRED"
    assert data["requires_confirmation"] is True
    assert data["executed"] is False
    assert data["risk_level"] == "CRITICAL"


# =========================
# Verify NO downstream call on unconfirmed
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_card_block_unconfirmed_no_downstream():
    """Unconfirmed card.block must NOT send request."""
    route = respx.post(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/cards/{TEST_CARD_ID}/block"
    ).mock(return_value=Response(200, json={}))

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "card.block",
        arguments={"card_id": str(TEST_CARD_ID)},
        confirmed=False,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        await client.post(
            "/api/v1/tools/execute", json=payload
        )

    assert route.call_count == 0


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_payment_create_unconfirmed_no_downstream():
    """Unconfirmed payment.create must NOT send request."""
    route = respx.post(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/payments"
    ).mock(return_value=Response(201, json={}))

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "payment.create",
        arguments={
            "source_account_id": str(TEST_ACCOUNT_ID),
            "beneficiary_id": str(TEST_BENEFICIARY_ID),
            "amount": "50.00",
            "currency": "USD",
        },
        confirmed=False,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        await client.post(
            "/api/v1/tools/execute", json=payload
        )

    assert route.call_count == 0


# =========================
# Confirmed execution
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_confirmed_high_risk_executes():
    """Confirmed HIGH-risk tool should execute."""
    respx.post(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/cards/{TEST_CARD_ID}/block"
    ).mock(
        return_value=Response(
            200,
            json={
                "id": str(TEST_CARD_ID),
                "status": "blocked",
            },
        )
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "card.block",
        arguments={"card_id": str(TEST_CARD_ID)},
        confirmed=True,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is True
    assert data["executed"] is True
    assert data["tool_name"] == "card.block"


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_confirmed_critical_executes():
    """Confirmed CRITICAL-risk tool should execute."""
    respx.post(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/payments"
    ).mock(
        return_value=Response(
            201,
            json={
                "id": str(uuid.uuid4()),
                "status": "pending",
            },
        )
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "payment.create",
        arguments={
            "source_account_id": str(TEST_ACCOUNT_ID),
            "beneficiary_id": str(TEST_BENEFICIARY_ID),
            "amount": "200.00",
            "currency": "USD",
        },
        confirmed=True,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is True
    assert data["executed"] is True


# =========================
# complaint.create (MEDIUM)
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_complaint_create_no_confirmation_needed():
    """MEDIUM-risk tool does not require confirmation."""
    respx.post(
        f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/complaints"
    ).mock(
        return_value=Response(
            201,
            json={
                "id": str(uuid.uuid4()),
                "status": "open",
            },
        )
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "complaint.create",
        arguments={
            "category": "billing",
            "subject": "Wrong charge",
            "description": "I was charged incorrectly on my last bill",
        },
        confirmed=False,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is True
    assert data["executed"] is True
    assert data["tool_name"] == "complaint.create"


# =========================
# beneficiary tools
# =========================


@pytest.mark.asyncio(loop_scope="function")
async def test_beneficiary_create_unconfirmed_blocked():
    """HIGH-risk beneficiary.create blocked unconfirmed."""
    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "beneficiary.create",
        arguments={
            "beneficiary_name": "Test Payee",
            "account_number": "12345678",
        },
        confirmed=False,
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
    assert data["error"]["code"] == "CONFIRMATION_REQUIRED"


@pytest.mark.asyncio(loop_scope="function")
async def test_beneficiary_deactivate_unconfirmed_blocked():
    """HIGH-risk beneficiary.deactivate blocked unconfirmed."""
    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "beneficiary.deactivate",
        arguments={
            "beneficiary_id": str(TEST_BENEFICIARY_ID)
        },
        confirmed=False,
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
    assert data["error"]["code"] == "CONFIRMATION_REQUIRED"


@pytest.mark.asyncio(loop_scope="function")
async def test_payment_cancel_unconfirmed_blocked():
    """HIGH-risk payment.cancel blocked unconfirmed."""
    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "payment.cancel",
        arguments={"payment_id": str(TEST_PAYMENT_ID)},
        confirmed=False,
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
    assert data["error"]["code"] == "CONFIRMATION_REQUIRED"
