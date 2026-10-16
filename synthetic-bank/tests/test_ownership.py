"""Customer ownership: customer A must never read or act on customer B's resources."""

import pytest

from tests.conftest import (
    ACCOUNT_A_ID,
    ACCOUNT_B_ID,
    CARD_A_ID,
    CARD_B_ID,
    CUSTOMER_A_ID,
    CUSTOMER_B_ID,
    LOAN_A_ID,
    LOAN_B_ID,
    headers_for,
)


# =========================
# Accounts
# =========================


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_can_read_own_account(client):
    resp = await client.get(f"/api/v1/accounts/{ACCOUNT_A_ID}", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(ACCOUNT_A_ID)
    assert body["customer_id"] == str(CUSTOMER_A_ID)


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_cannot_read_other_customers_account(client):
    resp = await client.get(f"/api/v1/accounts/{ACCOUNT_B_ID}", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 404


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_cannot_read_other_customers_balance(client):
    resp = await client.get(f"/api/v1/accounts/{ACCOUNT_B_ID}/balance", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 404


# =========================
# Cards
# =========================


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_can_read_own_card(client):
    resp = await client.get(f"/api/v1/cards/{CARD_A_ID}", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 200
    assert resp.json()["customer_id"] == str(CUSTOMER_A_ID)


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_cannot_read_other_customers_card(client):
    resp = await client.get(f"/api/v1/cards/{CARD_B_ID}", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 404


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_cannot_block_other_customers_card(client, db):
    resp = await client.post(f"/api/v1/cards/{CARD_B_ID}/block", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 404
    card_b = next(row for row in db.rows if getattr(row, "id", None) == CARD_B_ID)
    assert card_b.status == "active"
    assert db.commits == 0


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_can_block_own_card(client, db):
    resp = await client.post(f"/api/v1/cards/{CARD_A_ID}/block", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 200
    assert resp.json()["status"] == "blocked"
    assert db.commits == 1


# =========================
# Loans
# =========================


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_can_read_own_loan(client):
    resp = await client.get(f"/api/v1/loans/{LOAN_A_ID}", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 200
    assert resp.json()["customer_id"] == str(CUSTOMER_A_ID)


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_cannot_read_other_customers_loan(client):
    resp = await client.get(f"/api/v1/loans/{LOAN_B_ID}", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 404


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_cannot_list_other_customers_loans(client):
    resp = await client.get(f"/api/v1/loans/customer/{CUSTOMER_B_ID}", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 404


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_lists_only_own_loans(client):
    resp = await client.get(f"/api/v1/loans/customer/{CUSTOMER_A_ID}", headers=headers_for(CUSTOMER_A_ID))
    assert resp.status_code == 200
    assert [loan["id"] for loan in resp.json()] == [str(LOAN_A_ID)]


# =========================
# Customer context
# =========================


@pytest.mark.asyncio(loop_scope="function")
async def test_missing_customer_header_is_rejected(client):
    resp = await client.get(f"/api/v1/accounts/{ACCOUNT_A_ID}", headers=headers_for(None))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CUSTOMER_ID_REQUIRED"
