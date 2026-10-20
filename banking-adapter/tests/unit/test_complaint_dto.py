import uuid

import pytest

from app.schemas.complaint import (
    ComplaintDTO,
    ComplaintStatusDTO,
)


class TestComplaintDTO:

    def test_valid_complaint(self):
        data = {
            "id": "d1988217-adf1-4c19-be36-5348e527e6ae",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "complaint_number": "CMP000001",
            "category": "billing",
            "priority": "medium",
            "subject": "Incorrect charge",
            "description": "I was charged twice for the same transaction.",
            "status": "open",
            "assigned_to": None,
            "resolved_at": None,
            "created_at": "2026-04-01T10:00:00",
            "updated_at": "2026-04-01T10:00:00",
        }

        dto = ComplaintDTO.model_validate(data)

        assert dto.complaint_number == "CMP000001"
        assert dto.category == "billing"
        assert dto.priority == "medium"
        assert dto.status == "open"
        assert dto.assigned_to is None

    def test_resolved_complaint(self):
        data = {
            "id": "d1988217-adf1-4c19-be36-5348e527e6ae",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "complaint_number": "CMP000001",
            "category": "billing",
            "priority": "high",
            "subject": "Incorrect charge",
            "description": "I was charged twice.",
            "status": "resolved",
            "assigned_to": "44444444-4444-4444-4444-444444444444",
            "resolved_at": "2026-04-05T14:00:00",
            "created_at": "2026-04-01T10:00:00",
            "updated_at": "2026-04-05T14:00:00",
        }

        dto = ComplaintDTO.model_validate(data)

        assert dto.status == "resolved"
        assert dto.assigned_to is not None
        assert dto.resolved_at is not None

    def test_invalid_priority(self):
        data = {
            "id": "d1988217-adf1-4c19-be36-5348e527e6ae",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "complaint_number": "CMP000001",
            "category": "billing",
            "priority": "urgent",  # invalid
            "subject": "Test",
            "description": "Test complaint",
            "status": "open",
            "assigned_to": None,
            "resolved_at": None,
            "created_at": "2026-04-01T10:00:00",
            "updated_at": "2026-04-01T10:00:00",
        }

        with pytest.raises(Exception):
            ComplaintDTO.model_validate(data)

    def test_invalid_status(self):
        data = {
            "id": "d1988217-adf1-4c19-be36-5348e527e6ae",
            "tenant_id": "f498100f-80c4-467e-84ec-ebfe5470b442",
            "customer_id": "af339138-26c5-4dca-97ef-6b6a4183700d",
            "complaint_number": "CMP000001",
            "category": "billing",
            "priority": "medium",
            "subject": "Test",
            "description": "Test complaint",
            "status": "deleted",  # invalid
            "assigned_to": None,
            "resolved_at": None,
            "created_at": "2026-04-01T10:00:00",
            "updated_at": "2026-04-01T10:00:00",
        }

        with pytest.raises(Exception):
            ComplaintDTO.model_validate(data)


class TestComplaintStatusDTO:

    def test_valid_status(self):
        data = {
            "id": "d1988217-adf1-4c19-be36-5348e527e6ae",
            "complaint_number": "CMP000001",
            "status": "in_progress",
            "priority": "high",
            "assigned_to": "44444444-4444-4444-4444-444444444444",
            "resolved_at": None,
            "updated_at": "2026-04-02T08:00:00",
        }

        dto = ComplaintStatusDTO.model_validate(data)

        assert dto.status == "in_progress"
        assert dto.priority == "high"
        assert dto.resolved_at is None
