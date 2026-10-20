import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.schemas.loan import LoanDTO, LoanPaymentDTO, LoanStatusDTO


class TestLoanDTO:

    def test_valid_loan(self):
        data = {
            "id": "455f7ecc-afc2-4e80-886f-b928a74f9c34",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
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

        dto = LoanDTO.model_validate(data)

        assert dto.loan_number == "LN000011"
        assert dto.principal_amount == Decimal("500000.00")
        assert dto.interest_rate == Decimal("12.50")
        assert dto.start_date == date(2026, 1, 1)
        assert dto.maturity_date == date(2028, 1, 1)

    def test_nullable_maturity_date(self):
        data = {
            "id": "455f7ecc-afc2-4e80-886f-b928a74f9c34",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "loan_number": "LN000011",
            "loan_type": "revolving",
            "principal_amount": "500000.00",
            "outstanding_amount": "450000.00",
            "interest_rate": "12.50",
            "currency": "LKR",
            "status": "active",
            "start_date": "2026-01-01",
            "maturity_date": None,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }

        dto = LoanDTO.model_validate(data)

        assert dto.maturity_date is None

    def test_missing_required_field(self):
        data = {
            "id": "455f7ecc-afc2-4e80-886f-b928a74f9c34",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            # loan_number missing
            "loan_type": "personal",
            "principal_amount": "500000.00",
            "outstanding_amount": "450000.00",
            "interest_rate": "12.50",
            "currency": "LKR",
            "status": "active",
            "start_date": "2026-01-01",
            "maturity_date": None,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }

        with pytest.raises(Exception):
            LoanDTO.model_validate(data)


class TestLoanStatusDTO:

    def test_valid_status(self):
        data = {
            "id": "455f7ecc-afc2-4e80-886f-b928a74f9c34",
            "loan_number": "LN000011",
            "status": "active",
            "principal_amount": "500000.00",
            "outstanding_amount": "450000.00",
            "interest_rate": "12.50",
            "currency": "LKR",
            "maturity_date": "2028-01-01",
        }

        dto = LoanStatusDTO.model_validate(data)

        assert dto.loan_number == "LN000011"
        assert dto.status == "active"
        assert dto.outstanding_amount == Decimal("450000.00")


class TestLoanPaymentDTO:

    def test_valid_payment(self):
        data = {
            "id": "33333333-3333-3333-3333-333333333333",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "loan_id": "455f7ecc-afc2-4e80-886f-b928a74f9c34",
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

        dto = LoanPaymentDTO.model_validate(data)

        assert dto.installment_number == 1
        assert dto.amount == Decimal("25000.00")
        assert dto.principal_component == Decimal("20000.00")
        assert dto.interest_component == Decimal("5000.00")
        assert dto.status == "paid"

    def test_unpaid_payment(self):
        data = {
            "id": "33333333-3333-3333-3333-333333333333",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "loan_id": "455f7ecc-afc2-4e80-886f-b928a74f9c34",
            "payment_number": "LP000002",
            "installment_number": 2,
            "amount": "25000.00",
            "principal_component": "20500.00",
            "interest_component": "4500.00",
            "currency": "LKR",
            "due_date": "2026-03-01",
            "paid_at": None,
            "status": "pending",
            "created_at": "2026-01-01T00:00:00",
        }

        dto = LoanPaymentDTO.model_validate(data)

        assert dto.paid_at is None
        assert dto.status == "pending"
