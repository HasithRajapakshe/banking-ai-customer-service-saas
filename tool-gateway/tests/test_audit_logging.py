import logging
import uuid

import pytest

from app.schemas.context import ToolExecutionContext
from app.services.audit_service import audit_service, execution_status

CONTEXT = ToolExecutionContext(
    tenant_id=uuid.uuid4(),
    customer_id=uuid.uuid4(),
    user_id=uuid.uuid4(),
    correlation_id="corr-1",
)


async def log(caplog, **kwargs) -> logging.LogRecord:
    with caplog.at_level(logging.INFO, logger="tool_gateway.audit"):
        await audit_service.log_execution(
            tool_name="card.block", context=CONTEXT, risk_level="HIGH", **kwargs
        )
    records = [r for r in caplog.records if r.name == "tool_gateway.audit"]
    assert len(records) == 1
    return records[0]


@pytest.mark.asyncio(loop_scope="function")
async def test_held_for_confirmation_is_logged_as_awaiting_at_info(caplog):
    record = await log(caplog, executed=False, success=False, error_code="CONFIRMATION_REQUIRED")
    assert record.levelno == logging.INFO
    assert record.getMessage() == "Tool awaiting confirmation: card.block"


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize("error_code", ["TOOL_PROVIDER_UNAVAILABLE", None])
async def test_real_failures_are_still_warnings(caplog, error_code):
    record = await log(caplog, executed=True, success=False, error_code=error_code)
    assert record.levelno == logging.WARNING
    assert record.getMessage() == "Tool failed: card.block"


@pytest.mark.asyncio(loop_scope="function")
async def test_denials_are_logged_as_denied(caplog):
    record = await log(caplog, executed=False, success=False, error_code="PERMISSION_DENIED")
    assert record.levelno == logging.WARNING
    assert record.getMessage() == "Tool denied: card.block (PERMISSION_DENIED)"


@pytest.mark.asyncio(loop_scope="function")
async def test_success_is_logged_as_executed(caplog):
    record = await log(caplog, executed=True, success=True)
    assert record.levelno == logging.INFO
    assert record.getMessage() == "Tool executed: card.block"


@pytest.mark.parametrize("executed, success, code, expected", [
    (True, True, None, ("succeeded", "allowed")),
    (False, False, "CONFIRMATION_REQUIRED", ("requires_approval", "pending_confirmation")),
    (False, False, "PERMISSION_DENIED", ("denied", "denied")),
    (False, False, "CONFIRMATION_INVALID", ("denied", "denied")),
    (False, False, "INVALID_TOOL_ARGUMENTS", ("denied", "denied")),
    (True, False, "TOOL_PROVIDER_UNAVAILABLE", ("failed", "allowed")),
])
def test_execution_status_mapping(executed, success, code, expected):
    assert execution_status(executed, success, code) == expected
