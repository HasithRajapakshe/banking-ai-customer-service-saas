import uuid
from datetime import date, datetime

import pytest

from app.schemas.customer import CustomerDTO


class TestCustomerDTO:

    def test_valid_customer(self):
        data = {
            "id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_number": "CUST000001",
            "first_name": "Aravind",
            "last_name": "Kumar",
            "email": "aravind@example.com",
            "phone": "+94771234567",
            "date_of_birth": "1990-05-15",
            "status": "active",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }

        dto = CustomerDTO.model_validate(data)

        assert dto.id == uuid.UUID("af339138-26c5-4dca-97ef-6b6a4183700d")
        assert dto.first_name == "Aravind"
        assert dto.last_name == "Kumar"
        assert dto.email == "aravind@example.com"
        assert dto.date_of_birth == date(1990, 5, 15)
        assert dto.status == "active"

    def test_nullable_fields(self):
        data = {
            "id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_number": "CUST000001",
            "first_name": "Aravind",
            "last_name": "Kumar",
            "email": None,
            "phone": None,
            "date_of_birth": None,
            "status": "active",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }

        dto = CustomerDTO.model_validate(data)

        assert dto.email is None
        assert dto.phone is None
        assert dto.date_of_birth is None

    def test_missing_required_field(self):
        data = {
            "id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_number": "CUST000001",
            "first_name": "Aravind",
            # last_name missing
            "email": None,
            "phone": None,
            "date_of_birth": None,
            "status": "active",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }

        with pytest.raises(Exception):
            CustomerDTO.model_validate(data)
