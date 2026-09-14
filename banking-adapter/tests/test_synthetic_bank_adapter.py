import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.providers.synthetic_bank import SyntheticBankAdapter
from app.schemas.account import AccountBalanceDTO, AccountDTO
from app.schemas.beneficiary import BeneficiaryDTO
from app.schemas.card import CardDTO, CardTransactionDTO
from app.schemas.complaint import ComplaintDTO, ComplaintStatusDTO
from app.schemas.customer import CustomerDTO
from app.schemas.loan import LoanDTO, LoanPaymentDTO, LoanStatusDTO
from app.schemas.payment import PaymentDTO, PaymentStatusDTO
from app.schemas.transaction import AccountTransactionDTO


CUSTOMER_ID = uuid.UUID("af339138-26c5-4dca-97ef-6b6a4183700d")
TENANT_ID = uuid.UUID("f498100f-80c4-467e-84ec-ebfe5470b442")
ACCOUNT_ID = uuid.UUID("2284a359-5979-40dc-b496-644e13e97c74")
CARD_ID = uuid.UUID("d3ed4e35-fe60-436b-9a40-8ce42358161d")
PAYMENT_ID = uuid.UUID("74694f47-5afc-4a70-b1e0-058309351ee0")
BENEFICIARY_ID = uuid.UUID("9d129780-6ef1-4aa9-a886-604394b35870")
LOAN_ID = uuid.UUID("455f7ecc-afc2-4e80-886f-b928a74f9c34")
COMPLAINT_ID = uuid.UUID("d1988217-adf1-4c19-be36-5348e527e6ae")


def _customer_data():
    return {
        "id": str(CUSTOMER_ID),
        "tenant_id": str(TENANT_ID),
        "customer_number": "CUST000001",
        "first_name": "Aravind",
        "last_name": "Kumar",
        "email": "a@b.com",
        "phone": "+94771234567",
        "date_of_birth": "1990-05-15",
        "status": "active",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }


def _account_data():
    return {
        "id": str(ACCOUNT_ID),
        "tenant_id": str(TENANT_ID),
        "customer_id": str(CUSTOMER_ID),
        "account_number": "0010000000004",
        "account_type": "salary",
        "currency": "LKR",
        "current_balance": "150000.00",
        "available_balance": "145000.00",
        "status": "active",
        "opened_at": "2026-01-01T00:00:00",
        "closed_at": None,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }


def _balance_data():
    return {
        "account_id": str(ACCOUNT_ID),
        "account_number": "0010000000004",
        "currency": "LKR",
        "current_balance": "150000.00",
        "available_balance": "145000.00",
    }


def _txn_data():
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "tenant_id": str(TENANT_ID),
        "account_id": str(ACCOUNT_ID),
        "transaction_number": "TXN000001",
        "transaction_type": "transfer",
        "amount": "5000.00",
        "currency": "LKR",
        "direction": "debit",
        "balance_after": "145000.00",
        "description": "test",
        "merchant_name": None,
        "transaction_at": "2026-01-15T10:30:00",
        "created_at": "2026-01-15T10:30:00",
    }


def _card_data():
    return {
        "id": str(CARD_ID),
        "tenant_id": str(TENANT_ID),
        "customer_id": str(CUSTOMER_ID),
        "card_last4": "6768",
        "card_type": "debit",
        "expiry_month": 12,
        "expiry_year": 2028,
        "status": "blocked",
        "daily_limit": "100000.00",
        "issued_at": "2026-01-01T00:00:00",
        "blocked_at": "2026-06-01T12:00:00",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-06-01T12:00:00",
    }


def _card_txn_data():
    return {
        "id": "22222222-2222-2222-2222-222222222222",
        "tenant_id": str(TENANT_ID),
        "card_id": str(CARD_ID),
        "transaction_number": "CTXN000001",
        "amount": "2500.00",
        "currency": "LKR",
        "merchant_name": "Shop",
        "merchant_category": "retail",
        "status": "completed",
        "transaction_at": "2026-02-01T14:00:00",
        "created_at": "2026-02-01T14:00:00",
    }


def _payment_data():
    return {
        "id": str(PAYMENT_ID),
        "tenant_id": str(TENANT_ID),
        "customer_id": str(CUSTOMER_ID),
        "source_account_id": str(ACCOUNT_ID),
        "beneficiary_id": str(BENEFICIARY_ID),
        "payment_number": "PAY000001",
        "amount": "10000.00",
        "currency": "LKR",
        "payment_reference": "ref",
        "status": "completed",
        "idempotency_key": "key1",
        "requested_at": "2026-03-01T09:00:00",
        "completed_at": "2026-03-01T09:01:00",
        "created_at": "2026-03-01T09:00:00",
        "updated_at": "2026-03-01T09:01:00",
    }


def _payment_status_data():
    return {
        "id": str(PAYMENT_ID),
        "payment_number": "PAY000001",
        "status": "completed",
        "amount": "10000.00",
        "currency": "LKR",
        "requested_at": "2026-03-01T09:00:00",
        "completed_at": "2026-03-01T09:01:00",
    }


def _beneficiary_data():
    return {
        "id": str(BENEFICIARY_ID),
        "tenant_id": str(TENANT_ID),
        "customer_id": str(CUSTOMER_ID),
        "beneficiary_number": "BEN000001",
        "beneficiary_name": "John",
        "bank_name": "LNB",
        "account_number_masked": "****1234",
        "status": "active",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }


def _loan_data():
    return {
        "id": str(LOAN_ID),
        "tenant_id": str(TENANT_ID),
        "customer_id": str(CUSTOMER_ID),
        "loan_number": "LN000011",
        "loan_type": "personal",
        "principal_amount": "500000.00",
        "outstanding_amount": "450000.00",
        "interest_rate": "12.50",
        "currency": "LKR",
        "status": "active",
        "start_date": "2026-01-01",
        "maturity_date": "2028-01-01",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }


def _loan_status_data():
    return {
        "id": str(LOAN_ID),
        "loan_number": "LN000011",
        "status": "active",
        "principal_amount": "500000.00",
        "outstanding_amount": "450000.00",
        "interest_rate": "12.50",
        "currency": "LKR",
        "maturity_date": "2028-01-01",
    }


def _loan_payment_data():
    return {
        "id": "33333333-3333-3333-3333-333333333333",
        "tenant_id": str(TENANT_ID),
        "loan_id": str(LOAN_ID),
        "payment_number": "LP000001",
        "installment_number": 1,
        "amount": "25000.00",
        "principal_component": "20000.00",
        "interest_component": "5000.00",
        "currency": "LKR",
        "due_date": "2026-02-01",
        "paid_at": "2026-02-01T10:00:00",
        "status": "paid",
        "created_at": "2026-01-01T00:00:00",
    }


def _complaint_data():
    return {
        "id": str(COMPLAINT_ID),
        "tenant_id": str(TENANT_ID),
        "customer_id": str(CUSTOMER_ID),
        "complaint_number": "CMP000001",
        "category": "billing",
        "priority": "medium",
        "subject": "Issue",
        "description": "Description here",
        "status": "open",
        "assigned_to": None,
        "resolved_at": None,
        "created_at": "2026-04-01T10:00:00",
        "updated_at": "2026-04-01T10:00:00",
    }


def _complaint_status_data():
    return {
        "id": str(COMPLAINT_ID),
        "complaint_number": "CMP000001",
        "status": "in_progress",
        "priority": "high",
        "assigned_to": None,
        "resolved_at": None,
        "updated_at": "2026-04-02T08:00:00",
    }


@pytest.fixture
def adapter():
    a = SyntheticBankAdapter()
    a.client = AsyncMock()
    return a


# === Customer ===

@pytest.mark.asyncio
async def test_get_customer(adapter):
    adapter.client.request.return_value = _customer_data()
    result = await adapter.get_customer(CUSTOMER_ID)
    assert isinstance(result, CustomerDTO)
    assert result.first_name == "Aravind"


# === Accounts ===

@pytest.mark.asyncio
async def test_get_accounts(adapter):
    adapter.client.request.return_value = [_account_data()]
    result = await adapter.get_accounts(CUSTOMER_ID)
    assert isinstance(result, list)
    assert isinstance(result[0], AccountDTO)


@pytest.mark.asyncio
async def test_get_account(adapter):
    adapter.client.request.return_value = _account_data()
    result = await adapter.get_account(CUSTOMER_ID, ACCOUNT_ID)
    assert isinstance(result, AccountDTO)


@pytest.mark.asyncio
async def test_get_balance(adapter):
    adapter.client.request.return_value = _balance_data()
    result = await adapter.get_balance(CUSTOMER_ID, ACCOUNT_ID)
    assert isinstance(result, AccountBalanceDTO)


@pytest.mark.asyncio
async def test_get_account_transactions(adapter):
    adapter.client.request.return_value = [_txn_data()]
    result = await adapter.get_account_transactions(
        CUSTOMER_ID, ACCOUNT_ID,
    )
    assert isinstance(result[0], AccountTransactionDTO)


# === Cards ===

@pytest.mark.asyncio
async def test_get_card(adapter):
    adapter.client.request.return_value = _card_data()
    result = await adapter.get_card(CUSTOMER_ID, CARD_ID)
    assert isinstance(result, CardDTO)


@pytest.mark.asyncio
async def test_block_card(adapter):
    adapter.client.request.return_value = _card_data()
    result = await adapter.block_card(CUSTOMER_ID, CARD_ID)
    assert isinstance(result, CardDTO)


@pytest.mark.asyncio
async def test_get_card_transactions(adapter):
    adapter.client.request.return_value = [_card_txn_data()]
    result = await adapter.get_card_transactions(
        CUSTOMER_ID, CARD_ID,
    )
    assert isinstance(result[0], CardTransactionDTO)


# === Payments ===

@pytest.mark.asyncio
async def test_get_payment(adapter):
    adapter.client.request.return_value = _payment_data()
    result = await adapter.get_payment(CUSTOMER_ID, PAYMENT_ID)
    assert isinstance(result, PaymentDTO)


@pytest.mark.asyncio
async def test_list_payments(adapter):
    adapter.client.request.return_value = [_payment_data()]
    result = await adapter.list_payments(CUSTOMER_ID)
    assert isinstance(result[0], PaymentDTO)


@pytest.mark.asyncio
async def test_create_payment(adapter):
    adapter.client.request.return_value = _payment_data()
    result = await adapter.create_payment(
        CUSTOMER_ID, {"amount": "100"},
    )
    assert isinstance(result, PaymentDTO)


@pytest.mark.asyncio
async def test_get_payment_status(adapter):
    adapter.client.request.return_value = _payment_status_data()
    result = await adapter.get_payment_status(
        CUSTOMER_ID, PAYMENT_ID,
    )
    assert isinstance(result, PaymentStatusDTO)


@pytest.mark.asyncio
async def test_cancel_payment(adapter):
    adapter.client.request.return_value = _payment_data()
    result = await adapter.cancel_payment(
        CUSTOMER_ID, PAYMENT_ID,
    )
    assert isinstance(result, PaymentDTO)


# === Beneficiaries ===

@pytest.mark.asyncio
async def test_list_beneficiaries(adapter):
    adapter.client.request.return_value = [_beneficiary_data()]
    result = await adapter.list_beneficiaries(CUSTOMER_ID)
    assert isinstance(result[0], BeneficiaryDTO)


@pytest.mark.asyncio
async def test_get_beneficiary(adapter):
    adapter.client.request.return_value = _beneficiary_data()
    result = await adapter.get_beneficiary(
        CUSTOMER_ID, BENEFICIARY_ID,
    )
    assert isinstance(result, BeneficiaryDTO)


@pytest.mark.asyncio
async def test_create_beneficiary(adapter):
    adapter.client.request.return_value = _beneficiary_data()
    result = await adapter.create_beneficiary(
        CUSTOMER_ID, {"name": "test"},
    )
    assert isinstance(result, BeneficiaryDTO)


@pytest.mark.asyncio
async def test_deactivate_beneficiary(adapter):
    adapter.client.request.return_value = _beneficiary_data()
    result = await adapter.deactivate_beneficiary(
        CUSTOMER_ID, BENEFICIARY_ID,
    )
    assert isinstance(result, BeneficiaryDTO)


# === Loans ===

@pytest.mark.asyncio
async def test_get_loan(adapter):
    adapter.client.request.return_value = _loan_data()
    result = await adapter.get_loan(CUSTOMER_ID, LOAN_ID)
    assert isinstance(result, LoanDTO)


@pytest.mark.asyncio
async def test_list_loans(adapter):
    adapter.client.request.return_value = [_loan_data()]
    result = await adapter.list_loans(CUSTOMER_ID)
    assert isinstance(result[0], LoanDTO)


@pytest.mark.asyncio
async def test_get_loan_status(adapter):
    adapter.client.request.return_value = _loan_status_data()
    result = await adapter.get_loan_status(
        CUSTOMER_ID, LOAN_ID,
    )
    assert isinstance(result, LoanStatusDTO)


@pytest.mark.asyncio
async def test_get_loan_payments(adapter):
    adapter.client.request.return_value = [_loan_payment_data()]
    result = await adapter.get_loan_payments(
        CUSTOMER_ID, LOAN_ID,
    )
    assert isinstance(result[0], LoanPaymentDTO)


# === Complaints ===

@pytest.mark.asyncio
async def test_get_complaint(adapter):
    adapter.client.request.return_value = _complaint_data()
    result = await adapter.get_complaint(
        CUSTOMER_ID, COMPLAINT_ID,
    )
    assert isinstance(result, ComplaintDTO)


@pytest.mark.asyncio
async def test_list_complaints(adapter):
    adapter.client.request.return_value = [_complaint_data()]
    result = await adapter.list_complaints(CUSTOMER_ID)
    assert isinstance(result[0], ComplaintDTO)


@pytest.mark.asyncio
async def test_create_complaint(adapter):
    adapter.client.request.return_value = _complaint_data()
    result = await adapter.create_complaint(
        CUSTOMER_ID, {"subject": "test"},
    )
    assert isinstance(result, ComplaintDTO)


@pytest.mark.asyncio
async def test_get_complaint_status(adapter):
    adapter.client.request.return_value = _complaint_status_data()
    result = await adapter.get_complaint_status(
        CUSTOMER_ID, COMPLAINT_ID,
    )
    assert isinstance(result, ComplaintStatusDTO)
