import uuid
from decimal import Decimal

import pytest

from app.schemas.payment import PaymentDTO, PaymentStatusDTO


class TestPaymentDTO:

    def test_valid_payment(self):
        data = {
            "id": "74694f47-5afc-4a70-b1e0-058309351ee0",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "source_account_id": "2284a359-5979-40dc-b496-644e13e97c74",
            "beneficiary_id": "9d129780-6ef1-4aa9-a886-604394b35870",
            "payment_number": "PAY000001",
            "amount": "10000.00",
            "currency": "LKR",
            "payment_reference": "Invoice #123",
            "status": "completed",
            "idempotency_key": "unique-key-001",
            "requested_at": "2026-03-01T09:00:00",
            "completed_at": "2026-03-01T09:01:00",
            "created_at": "2026-03-01T09:00:00",
            "updated_at": "2026-03-01T09:01:00",
        }

        dto = PaymentDTO.model_validate(data)

        assert dto.payment_number == "PAY000001"
        assert dto.amount == Decimal("10000.00")
        assert dto.status == "completed"
        assert dto.idempotency_key == "unique-key-001"

    def test_nullable_fields(self):
        data = {
            "id": "74694f47-5afc-4a70-b1e0-058309351ee0",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "source_account_id": "2284a359-5979-40dc-b496-644e13e97c74",
            "beneficiary_id": "9d129780-6ef1-4aa9-a886-604394b35870",
            "payment_number": "PAY000001",
            "amount": "10000.00",
            "currency": "LKR",
            "payment_reference": None,
            "status": "pending",
            "idempotency_key": None,
            "requested_at": "2026-03-01T09:00:00",
            "completed_at": None,
            "created_at": "2026-03-01T09:00:00",
            "updated_at": "2026-03-01T09:00:00",
        }

        dto = PaymentDTO.model_validate(data)

        assert dto.payment_reference is None
        assert dto.idempotency_key is None
        assert dto.completed_at is None

    def test_missing_required_field(self):
        data = {
            "id": "74694f47-5afc-4a70-b1e0-058309351ee0",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            # source_account_id missing
            "beneficiary_id": "9d129780-6ef1-4aa9-a886-604394b35870",
            "payment_number": "PAY000001",
            "amount": "10000.00",
            "currency": "LKR",
            "payment_reference": None,
            "status": "pending",
            "idempotency_key": None,
            "requested_at": "2026-03-01T09:00:00",
            "completed_at": None,
            "created_at": "2026-03-01T09:00:00",
            "updated_at": "2026-03-01T09:00:00",
        }

        with pytest.raises(Exception):
            PaymentDTO.model_validate(data)


class TestPaymentStatusDTO:

    def test_valid_status(self):
        data = {
            "id": "74694f47-5afc-4a70-b1e0-058309351ee0",
            "payment_number": "PAY000001",
            "status": "completed",
            "amount": "10000.00",
            "currency": "LKR",
            "requested_at": "2026-03-01T09:00:00",
            "completed_at": "2026-03-01T09:01:00",
        }

        dto = PaymentStatusDTO.model_validate(data)

        assert dto.status == "completed"
        assert dto.amount == Decimal("10000.00")

    def test_pending_status(self):
        data = {
            "id": "74694f47-5afc-4a70-b1e0-058309351ee0",
            "payment_number": "PAY000001",
            "status": "pending",
            "amount": "10000.00",
            "currency": "LKR",
            "requested_at": "2026-03-01T09:00:00",
            "completed_at": None,
        }

        dto = PaymentStatusDTO.model_validate(data)

        assert dto.completed_at is None
