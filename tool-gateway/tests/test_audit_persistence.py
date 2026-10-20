"""Every execution is persisted; a failing audit store never breaks the request."""

import logging
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import settings
from app.repositories.audit_repository import mask_arguments
from main import app
from tests.conftest import TEST_CARD_ID, TEST_CUSTOMER_ID, make_execute_payload

BASE = settings.banking_adapter_base_url.rstrip("/")


async def execute(payload: dict) -> dict:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return (await client.post("/api/v1/tools/execute", json=payload)).json()


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_executed_tool_is_recorded_as_succeeded(audit_records):
    respx.get(f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}/cards").mock(return_value=Response(200, json=[]))

    await execute(make_execute_payload("card.list"))

    (record,) = audit_records
    assert (record.tool_name, record.status, record.authorization_result) == ("card.list", "succeeded", "allowed")
    assert record.executed is True and record.success is True
    assert record.customer_id == TEST_CUSTOMER_ID


@pytest.mark.asyncio(loop_scope="function")
async def test_held_tool_is_recorded_as_requires_approval(audit_records):
    await execute(make_execute_payload("card.block", arguments={"card_id": str(TEST_CARD_ID)}))

    (record,) = audit_records
    assert (record.status, record.authorization_result) == ("requires_approval", "pending_confirmation")
    assert record.risk_level == "HIGH"
    assert record.arguments == {"card_id": str(TEST_CARD_ID)}


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_provider_failure_is_recorded_as_failed(audit_records):
    respx.get(f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}/cards").mock(return_value=Response(503))

    await execute(make_execute_payload("card.list"))

    (record,) = audit_records
    assert record.status == "failed"
    assert record.executed is True


@pytest.mark.asyncio(loop_scope="function")
async def test_invalid_arguments_are_recorded_as_denied(audit_records):
    await execute(make_execute_payload("card.get_details", arguments={"card_id": "nope"}))

    (record,) = audit_records
    assert (record.status, record.error_code) == ("denied", "INVALID_TOOL_ARGUMENTS")


@pytest.mark.asyncio(loop_scope="function")
@respx.mock
async def test_audit_store_failure_does_not_break_the_request(caplog):
    respx.get(f"{BASE}/api/v1/customers/{TEST_CUSTOMER_ID}/cards").mock(return_value=Response(200, json=[{"id": "c1"}]))

    with patch(
        "app.services.audit_service.audit_repository.record",
        new=AsyncMock(side_effect=ConnectionError("database is down")),
    ), caplog.at_level(logging.ERROR, logger="tool_gateway.audit"):
        body = await execute(make_execute_payload("card.list"))

    assert body["success"] is True
    assert body["data"] == [{"id": "c1"}]
    assert "AUDIT WRITE FAILED for card.list" in caplog.text
    assert "database is down" in caplog.text


def test_long_digit_strings_are_masked_in_audit_arguments():
    masked = mask_arguments({"account_number": "8001234567", "amount": "5000.00", "beneficiary_name": "Kamal"})
    assert masked == {"account_number": "******4567", "amount": "5000.00", "beneficiary_name": "Kamal"}
