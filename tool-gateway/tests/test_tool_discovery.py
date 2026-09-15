import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio(loop_scope="function")
async def test_list_tools():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/tools")

    assert response.status_code == 200

    tools = response.json()
    assert isinstance(tools, list)
    assert len(tools) == 25

    names = {t["name"] for t in tools}
    assert "account.get_balance" in names
    assert "payment.create" in names
    assert "customer.get_profile" in names

    # Verify each tool has required metadata
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "risk_level" in tool
        assert "requires_confirmation" in tool
        assert "permission" in tool


@pytest.mark.asyncio(loop_scope="function")
async def test_get_tool_by_name():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/tools/account.get_balance"
        )

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "account.get_balance"
    assert data["risk_level"] == "LOW"
    assert data["permission"] == "account.balance.read"
    assert data["requires_confirmation"] is False


@pytest.mark.asyncio(loop_scope="function")
async def test_get_tool_not_found():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/tools/nonexistent.tool"
        )

    assert response.status_code == 404
