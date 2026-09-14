import uuid
from decimal import Decimal

import pytest

from app.schemas.account import AccountBalanceDTO, AccountDTO


class TestAccountDTO:

    def test_valid_account(self):
        data = {
            "id": "2284a359-5979-40dc-b496-644e13e97c74",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
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

        dto = AccountDTO.model_validate(data)

        assert dto.account_number == "0010000000004"
        assert dto.account_type == "salary"
        assert dto.current_balance == Decimal("150000.00")
        assert dto.closed_at is None

    def test_missing_required_field(self):
        data = {
            "id": "2284a359-5979-40dc-b496-644e13e97c74",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            # customer_id missing
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

        with pytest.raises(Exception):
            AccountDTO.model_validate(data)


class TestAccountBalanceDTO:

    def test_valid_balance(self):
        data = {
            "account_id": "2284a359-5979-40dc-b496-644e13e97c74",
            "account_number": "0010000000004",
            "currency": "LKR",
            "current_balance": "150000.00",
            "available_balance": "145000.00",
        }

        dto = AccountBalanceDTO.model_validate(data)

        assert dto.current_balance == Decimal("150000.00")
        assert dto.available_balance == Decimal("145000.00")
