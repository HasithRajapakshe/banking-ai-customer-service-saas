import uuid

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestCorrelationId:

    def test_provided_correlation_id_preserved(self, client):
        response = client.get(
            "/health",
            headers={"X-Correlation-ID": "my-test-id-123"},
        )

        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == "my-test-id-123"

    def test_missing_correlation_id_generated(self, client):
        response = client.get("/health")

        assert response.status_code == 200

        corr_id = response.headers.get("X-Correlation-ID")
        assert corr_id is not None
        assert len(corr_id) > 0

        # Should be a valid UUID
        uuid.UUID(corr_id)

    def test_empty_correlation_id_generates_new(self, client):
        response = client.get(
            "/health",
            headers={"X-Correlation-ID": ""},
        )

        assert response.status_code == 200

        corr_id = response.headers.get("X-Correlation-ID")
        assert corr_id is not None
        assert corr_id != ""

        uuid.UUID(corr_id)

    def test_whitespace_correlation_id_generates_new(self, client):
        response = client.get(
            "/health",
            headers={"X-Correlation-ID": "   "},
        )

        assert response.status_code == 200

        corr_id = response.headers.get("X-Correlation-ID")
        assert corr_id is not None
        assert corr_id.strip() != ""
