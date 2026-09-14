import uuid

import pytest

from app.schemas.beneficiary import BeneficiaryDTO


class TestBeneficiaryDTO:

    def test_valid_beneficiary(self):
        data = {
            "id": "9d129780-6ef1-4aa9-a886-604394b35870",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "beneficiary_number": "BEN000001",
            "beneficiary_name": "John Doe",
            "bank_name": "Lanka National Bank",
            "account_number_masked": "****1234",
            "status": "active",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }

        dto = BeneficiaryDTO.model_validate(data)

        assert dto.beneficiary_name == "John Doe"
        assert dto.bank_name == "Lanka National Bank"
        assert dto.account_number_masked == "****1234"
        assert dto.status == "active"

    def test_nullable_fields(self):
        data = {
            "id": "9d129780-6ef1-4aa9-a886-604394b35870",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "beneficiary_number": "BEN000001",
            "beneficiary_name": "John Doe",
            "bank_name": None,
            "account_number_masked": None,
            "status": "active",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }

        dto = BeneficiaryDTO.model_validate(data)

        assert dto.bank_name is None
        assert dto.account_number_masked is None

    def test_missing_required_field(self):
        data = {
            "id": "9d129780-6ef1-4aa9-a886-604394b35870",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            # customer_id missing
            "beneficiary_number": "BEN000001",
            "beneficiary_name": "John Doe",
            "bank_name": None,
            "account_number_masked": None,
            "status": "active",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }

        with pytest.raises(Exception):
            BeneficiaryDTO.model_validate(data)
