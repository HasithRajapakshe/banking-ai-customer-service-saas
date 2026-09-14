import uuid
from decimal import Decimal

import pytest

from app.schemas.transaction import AccountTransactionDTO


class TestAccountTransactionDTO:

    def test_valid_transaction(self):
        data = {
            "id": "11111111-1111-1111-1111-111111111111",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "account_id": "2284a359-5979-40dc-b496-644e13e97c74",
            "transaction_number": "TXN000001",
            "transaction_type": "transfer",
            "amount": "5000.00",
            "currency": "LKR",
            "direction": "debit",
            "balance_after": "145000.00",
            "description": "Salary transfer",
            "merchant_name": None,
            "transaction_at": "2026-01-15T10:30:00",
            "created_at": "2026-01-15T10:30:00",
        }

        dto = AccountTransactionDTO.model_validate(data)

        assert dto.transaction_type == "transfer"
        assert dto.amount == Decimal("5000.00")
        assert dto.direction == "debit"
        assert dto.merchant_name is None

    def test_missing_required_field(self):
        data = {
            "id": "11111111-1111-1111-1111-111111111111",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "account_id": "2284a359-5979-40dc-b496-644e13e97c74",
            # transaction_number missing
            "transaction_type": "transfer",
            "amount": "5000.00",
            "currency": "LKR",
            "direction": "debit",
            "balance_after": "145000.00",
            "description": None,
            "merchant_name": None,
            "transaction_at": "2026-01-15T10:30:00",
            "created_at": "2026-01-15T10:30:00",
        }

        with pytest.raises(Exception):
            AccountTransactionDTO.model_validate(data)
