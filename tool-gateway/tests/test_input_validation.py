import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from tests.conftest import make_execute_payload, TEST_ACCOUNT_ID


@pytest.mark.asyncio(loop_scope="function")
async def test_strict_extra_field_rejection():
    """Extra fields in arguments should be rejected."""
    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "account.get_balance",
        arguments={
            "account_id": str(TEST_ACCOUNT_ID),
            "extra_field": "should_fail",
        },
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/tools/execute",
            json=payload,
        )

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOOL_ARGUMENTS"
    assert data["executed"] is False


@pytest.mark.asyncio(loop_scope="function")
async def test_malformed_uuid_rejection():
    """Malformed UUIDs should be rejected."""
    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "account.get_balance",
        arguments={"account_id": "not-a-uuid"},
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/tools/execute",
            json=payload,
        )

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOOL_ARGUMENTS"


@pytest.mark.asyncio(loop_scope="function")
async def test_customer_id_not_in_tool_arguments():
    """customer_id must NOT be accepted in tool arguments.

    customer_id comes from ToolExecutionContext only.
    """
    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "customer.get_profile",
        arguments={
            "customer_id": str(uuid.uuid4()),
        },
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/tools/execute",
            json=payload,
        )

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOOL_ARGUMENTS"


@pytest.mark.asyncio(loop_scope="function")
async def test_unknown_tool():
    """Unknown tool name returns TOOL_NOT_FOUND."""
    transport = ASGITransport(app=app)
    payload = make_execute_payload("fake.tool")

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/tools/execute",
            json=payload,
        )

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOOL_NOT_FOUND"
    assert data["executed"] is False


@pytest.mark.asyncio(loop_scope="function")
async def test_empty_input_rejects_extra_fields():
    """EmptyInput tools must reject any arguments."""
    transport = ASGITransport(app=app)
    payload = make_execute_payload(
        "customer.get_profile",
        arguments={"any_param": "value"},
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/tools/execute",
            json=payload,
        )

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOOL_ARGUMENTS"


@pytest.mark.asyncio(loop_scope="function")
async def test_pagination_limit_bounds():
    """Limit must be between 1 and 100."""
    transport = ASGITransport(app=app)

    # limit = 0 should fail
    payload = make_execute_payload(
        "account.list",
        arguments={"limit": 0},
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/tools/execute",
            json=payload,
        )

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOOL_ARGUMENTS"


@pytest.mark.asyncio(loop_scope="function")
async def test_pagination_limit_above_max():
    """Limit > 100 should fail."""
    transport = ASGITransport(app=app)

    payload = make_execute_payload(
        "account.list",
        arguments={"limit": 101},
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/tools/execute",
            json=payload,
        )

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOOL_ARGUMENTS"
