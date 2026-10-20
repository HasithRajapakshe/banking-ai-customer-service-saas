import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio(loop_scope="function")
async def test_health_endpoint():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "tool-gateway"
