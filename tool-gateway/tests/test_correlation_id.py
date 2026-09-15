import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio(loop_scope="function")
async def test_correlation_id_generated_when_missing():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    cid = response.headers.get("X-Correlation-ID")
    assert cid is not None

    # Should be a valid UUID4
    uuid.UUID(cid)


@pytest.mark.asyncio(loop_scope="function")
async def test_provided_correlation_id_preserved():
    transport = ASGITransport(app=app)
    expected = str(uuid.uuid4())

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/health",
            headers={"X-Correlation-ID": expected},
        )

    assert response.headers["X-Correlation-ID"] == expected


@pytest.mark.asyncio(loop_scope="function")
async def test_empty_correlation_id_generates_new():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/health",
            headers={"X-Correlation-ID": "  "},
        )

    cid = response.headers["X-Correlation-ID"]
    assert cid.strip() != ""

    uuid.UUID(cid)
