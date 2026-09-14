import uuid
from decimal import Decimal

import pytest

from app.schemas.card import CardDTO, CardTransactionDTO


class TestCardDTO:

    def test_valid_card(self):
        data = {
            "id": "d3ed4e35-fe60-436b-9a40-8ce42358161d",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
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

        dto = CardDTO.model_validate(data)

        assert dto.card_last4 == "6768"
        assert dto.card_type == "debit"
        assert dto.status == "blocked"
        assert dto.daily_limit == Decimal("100000.00")

    def test_nullable_fields(self):
        data = {
            "id": "d3ed4e35-fe60-436b-9a40-8ce42358161d",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "card_last4": "6768",
            "card_type": "debit",
            "expiry_month": 12,
            "expiry_year": 2028,
            "status": "active",
            "daily_limit": None,
            "issued_at": "2026-01-01T00:00:00",
            "blocked_at": None,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }

        dto = CardDTO.model_validate(data)

        assert dto.daily_limit is None
        assert dto.blocked_at is None


class TestCardTransactionDTO:

    def test_valid_card_transaction(self):
        data = {
            "id": "22222222-2222-2222-2222-222222222222",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "card_id": "d3ed4e35-fe60-436b-9a40-8ce42358161d",
            "transaction_number": "CTXN000001",
            "amount": "2500.00",
            "currency": "LKR",
            "merchant_name": "Supermarket",
            "merchant_category": "groceries",
            "status": "completed",
            "transaction_at": "2026-02-01T14:00:00",
            "created_at": "2026-02-01T14:00:00",
        }

        dto = CardTransactionDTO.model_validate(data)

        assert dto.amount == Decimal("2500.00")
        assert dto.merchant_name == "Supermarket"
        assert dto.status == "completed"
