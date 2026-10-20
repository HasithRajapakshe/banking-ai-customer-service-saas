import uuid

from fastapi import APIRouter, HTTPException, Request

from app.core.errors import BankingAdapterError
from app.factory import get_banking_provider


dev_router = APIRouter(
    prefix="/test",
    tags=["Development"],
)


# =========================
# Helper
# =========================

def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", None) or ""


def _raise_adapter_error(exc: BankingAdapterError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
            "correlation_id": exc.correlation_id,
        },
    )


# =========================
# Customer
# =========================

@dev_router.get("/customer/{customer_id}")
async def test_customer(
    customer_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_customer(
            customer_id=customer_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Customer Accounts
# =========================

@dev_router.get("/customer/{customer_id}/accounts")
async def test_customer_accounts(
    customer_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_accounts(
            customer_id=customer_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Account Details
# =========================

@dev_router.get(
    "/customer/{customer_id}/accounts/{account_id}"
)
async def test_account(
    customer_id: uuid.UUID,
    account_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_account(
            customer_id=customer_id,
            account_id=account_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Account Balance
# =========================

@dev_router.get(
    "/customer/{customer_id}/accounts/{account_id}/balance"
)
async def test_account_balance(
    customer_id: uuid.UUID,
    account_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_balance(
            customer_id=customer_id,
            account_id=account_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Account Transactions
# =========================

@dev_router.get(
    "/customer/{customer_id}/accounts/"
    "{account_id}/transactions"
)
async def test_account_transactions(
    customer_id: uuid.UUID,
    account_id: uuid.UUID,
    request: Request,
    limit: int = 20,
    offset: int = 0,
):
    provider = get_banking_provider()

    try:
        return await provider.get_account_transactions(
            customer_id=customer_id,
            account_id=account_id,
            limit=limit,
            offset=offset,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Get Card
# =========================

@dev_router.get(
    "/customer/{customer_id}/cards/{card_id}"
)
async def test_card(
    customer_id: uuid.UUID,
    card_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_card(
            customer_id=customer_id,
            card_id=card_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Card Transactions
# =========================

@dev_router.get(
    "/customer/{customer_id}/cards/{card_id}/transactions"
)
async def test_card_transactions(
    customer_id: uuid.UUID,
    card_id: uuid.UUID,
    request: Request,
    limit: int = 20,
    offset: int = 0,
):
    provider = get_banking_provider()

    try:
        return await provider.get_card_transactions(
            customer_id=customer_id,
            card_id=card_id,
            limit=limit,
            offset=offset,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Block Card
# =========================

@dev_router.post(
    "/customer/{customer_id}/cards/{card_id}/block"
)
async def test_block_card(
    customer_id: uuid.UUID,
    card_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.block_card(
            customer_id=customer_id,
            card_id=card_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# List Payments
# =========================

@dev_router.get("/customer/{customer_id}/payments")
async def test_list_payments(
    customer_id: uuid.UUID,
    request: Request,
    limit: int = 20,
    offset: int = 0,
):
    provider = get_banking_provider()

    try:
        return await provider.list_payments(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Get Payment
# =========================

@dev_router.get(
    "/customer/{customer_id}/payments/{payment_id}"
)
async def test_get_payment(
    customer_id: uuid.UUID,
    payment_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_payment(
            customer_id=customer_id,
            payment_id=payment_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Payment Status
# =========================

@dev_router.get(
    "/customer/{customer_id}/payments/"
    "{payment_id}/status"
)
async def test_payment_status(
    customer_id: uuid.UUID,
    payment_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_payment_status(
            customer_id=customer_id,
            payment_id=payment_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Create Payment
# =========================

@dev_router.post("/customer/{customer_id}/payments")
async def test_create_payment(
    customer_id: uuid.UUID,
    payment_data: dict,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.create_payment(
            customer_id=customer_id,
            payment_data=payment_data,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Cancel Payment
# =========================

@dev_router.post(
    "/customer/{customer_id}/payments/"
    "{payment_id}/cancel"
)
async def test_cancel_payment(
    customer_id: uuid.UUID,
    payment_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.cancel_payment(
            customer_id=customer_id,
            payment_id=payment_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# List Beneficiaries
# =========================

@dev_router.get("/customer/{customer_id}/beneficiaries")
async def test_list_beneficiaries(
    customer_id: uuid.UUID,
    request: Request,
    limit: int = 20,
    offset: int = 0,
):
    provider = get_banking_provider()

    try:
        return await provider.list_beneficiaries(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Get Beneficiary
# =========================

@dev_router.get(
    "/customer/{customer_id}/beneficiaries/"
    "{beneficiary_id}"
)
async def test_get_beneficiary(
    customer_id: uuid.UUID,
    beneficiary_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_beneficiary(
            customer_id=customer_id,
            beneficiary_id=beneficiary_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Create Beneficiary
# =========================

@dev_router.post(
    "/customer/{customer_id}/beneficiaries"
)
async def test_create_beneficiary(
    customer_id: uuid.UUID,
    beneficiary_data: dict,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.create_beneficiary(
            customer_id=customer_id,
            beneficiary_data=beneficiary_data,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Deactivate Beneficiary
# =========================

@dev_router.post(
    "/customer/{customer_id}/beneficiaries/"
    "{beneficiary_id}/deactivate"
)
async def test_deactivate_beneficiary(
    customer_id: uuid.UUID,
    beneficiary_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.deactivate_beneficiary(
            customer_id=customer_id,
            beneficiary_id=beneficiary_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# List Loans
# =========================

@dev_router.get("/customer/{customer_id}/loans")
async def test_list_loans(
    customer_id: uuid.UUID,
    request: Request,
    limit: int = 20,
    offset: int = 0,
):
    provider = get_banking_provider()

    try:
        return await provider.list_loans(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Get Loan
# =========================

@dev_router.get(
    "/customer/{customer_id}/loans/{loan_id}"
)
async def test_get_loan(
    customer_id: uuid.UUID,
    loan_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_loan(
            customer_id=customer_id,
            loan_id=loan_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Loan Status
# =========================

@dev_router.get(
    "/customer/{customer_id}/loans/{loan_id}/status"
)
async def test_loan_status(
    customer_id: uuid.UUID,
    loan_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_loan_status(
            customer_id=customer_id,
            loan_id=loan_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Loan Payments
# =========================

@dev_router.get(
    "/customer/{customer_id}/loans/{loan_id}/payments"
)
async def test_loan_payments(
    customer_id: uuid.UUID,
    loan_id: uuid.UUID,
    request: Request,
    limit: int = 20,
    offset: int = 0,
):
    provider = get_banking_provider()

    try:
        return await provider.get_loan_payments(
            customer_id=customer_id,
            loan_id=loan_id,
            limit=limit,
            offset=offset,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# List Complaints
# =========================

@dev_router.get("/customer/{customer_id}/complaints")
async def test_list_complaints(
    customer_id: uuid.UUID,
    request: Request,
    limit: int = 20,
    offset: int = 0,
):
    provider = get_banking_provider()

    try:
        return await provider.list_complaints(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Get Complaint
# =========================

@dev_router.get(
    "/customer/{customer_id}/complaints/{complaint_id}"
)
async def test_get_complaint(
    customer_id: uuid.UUID,
    complaint_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_complaint(
            customer_id=customer_id,
            complaint_id=complaint_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Complaint Status
# =========================

@dev_router.get(
    "/customer/{customer_id}/complaints/"
    "{complaint_id}/status"
)
async def test_complaint_status(
    customer_id: uuid.UUID,
    complaint_id: uuid.UUID,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.get_complaint_status(
            customer_id=customer_id,
            complaint_id=complaint_id,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)


# =========================
# Create Complaint
# =========================

@dev_router.post(
    "/customer/{customer_id}/complaints"
)
async def test_create_complaint(
    customer_id: uuid.UUID,
    complaint_data: dict,
    request: Request,
):
    provider = get_banking_provider()

    try:
        return await provider.create_complaint(
            customer_id=customer_id,
            complaint_data=complaint_data,
            correlation_id=_correlation_id(request),
        )
    except BankingAdapterError as exc:
        _raise_adapter_error(exc)
