"""Tests for all 19 read-only tools using respx mocks."""

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
    TEST_LOAN_ID,
    TEST_PAYMENT_ID,
    TEST_TENANT_ID,
    make_execute_payload,
)

BASE = "http://127.0.0.1:8002"


def _mock_get(path: str, json_data):
    respx.get(f"{BASE}{path}").mock(
        return_value=Response(200, json=json_data)
    )


# =========================
# customer.get_profile
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_customer_get_profile():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}",
        {"id": str(TEST_CUSTOMER_ID), "name": "Test"},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload("customer.get_profile")

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is True
    assert data["tool_name"] == "customer.get_profile"
    assert data["executed"] is True


# =========================
# account.list
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_account_list():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}/accounts",
        [{"id": str(TEST_ACCOUNT_ID)}],
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload("account.list")

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is True
    assert data["tool_name"] == "account.list"


# =========================
# account.get_details
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_account_get_details():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/accounts/{TEST_ACCOUNT_ID}",
        {"id": str(TEST_ACCOUNT_ID), "type": "savings"},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "account.get_details",
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
    assert data["success"] is True
    assert data["tool_name"] == "account.get_details"


# =========================
# account.get_balance
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_account_get_balance():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/accounts/{TEST_ACCOUNT_ID}/balance",
        {"balance": "1000.00", "currency": "USD"},
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
    assert data["success"] is True
    assert data["tool_name"] == "account.get_balance"
    assert data["risk_level"] == "LOW"


# =========================
# account.get_transactions
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_account_get_transactions():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/accounts/{TEST_ACCOUNT_ID}/transactions",
        [{"id": str(uuid.uuid4()), "amount": "50.00"}],
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "account.get_transactions",
        arguments={
            "account_id": str(TEST_ACCOUNT_ID),
            "limit": 10,
        },
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
    assert data["tool_name"] == "account.get_transactions"


# =========================
# card.get_details
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_card_get_details():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/cards/{TEST_CARD_ID}",
        {"id": str(TEST_CARD_ID), "status": "active"},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "card.get_details",
        arguments={"card_id": str(TEST_CARD_ID)},
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
    assert data["tool_name"] == "card.get_details"


# =========================
# card.get_transactions
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_card_get_transactions():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/cards/{TEST_CARD_ID}/transactions",
        [],
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "card.get_transactions",
        arguments={"card_id": str(TEST_CARD_ID)},
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
    assert data["tool_name"] == "card.get_transactions"


# =========================
# beneficiary.list
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_beneficiary_list():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/beneficiaries",
        [],
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload("beneficiary.list")

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is True
    assert data["tool_name"] == "beneficiary.list"


# =========================
# beneficiary.get
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_beneficiary_get():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/beneficiaries/{TEST_BENEFICIARY_ID}",
        {"id": str(TEST_BENEFICIARY_ID)},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "beneficiary.get",
        arguments={
            "beneficiary_id": str(TEST_BENEFICIARY_ID)
        },
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
    assert data["tool_name"] == "beneficiary.get"


# =========================
# payment.list
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_payment_list():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}/payments",
        [],
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload("payment.list")

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is True


# =========================
# payment.get
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_payment_get():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/payments/{TEST_PAYMENT_ID}",
        {"id": str(TEST_PAYMENT_ID)},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "payment.get",
        arguments={"payment_id": str(TEST_PAYMENT_ID)},
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


# =========================
# payment.get_status
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_payment_get_status():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/payments/{TEST_PAYMENT_ID}/status",
        {"status": "completed"},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "payment.get_status",
        arguments={"payment_id": str(TEST_PAYMENT_ID)},
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


# =========================
# loan.list
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_loan_list():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}/loans",
        [],
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload("loan.list")

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is True


# =========================
# loan.get
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_loan_get():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/loans/{TEST_LOAN_ID}",
        {"id": str(TEST_LOAN_ID)},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "loan.get",
        arguments={"loan_id": str(TEST_LOAN_ID)},
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


# =========================
# loan.get_status
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_loan_get_status():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/loans/{TEST_LOAN_ID}/status",
        {"status": "active"},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "loan.get_status",
        arguments={"loan_id": str(TEST_LOAN_ID)},
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


# =========================
# loan.get_payments
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_loan_get_payments():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/loans/{TEST_LOAN_ID}/payments",
        [],
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "loan.get_payments",
        arguments={"loan_id": str(TEST_LOAN_ID)},
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


# =========================
# complaint.list
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_complaint_list():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/complaints",
        [],
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload("complaint.list")

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/tools/execute", json=payload
        )

    data = resp.json()
    assert data["success"] is True


# =========================
# complaint.get
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_complaint_get():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/complaints/{TEST_COMPLAINT_ID}",
        {"id": str(TEST_COMPLAINT_ID)},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "complaint.get",
        arguments={
            "complaint_id": str(TEST_COMPLAINT_ID)
        },
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


# =========================
# complaint.get_status
# =========================


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_complaint_get_status():
    _mock_get(
        f"/api/v1/customers/{TEST_CUSTOMER_ID}"
        f"/complaints/{TEST_COMPLAINT_ID}/status",
        {"status": "open"},
    )

    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "complaint.get_status",
        arguments={
            "complaint_id": str(TEST_COMPLAINT_ID)
        },
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
