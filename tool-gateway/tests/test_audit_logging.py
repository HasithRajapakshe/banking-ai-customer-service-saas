import logging
import uuid

import pytest

from app.schemas.context import ToolExecutionContext
from app.services.audit_service import audit_service

CONTEXT = ToolExecutionContext(
    tenant_id=uuid.uuid4(),
    customer_id=uuid.uuid4(),
    user_id=uuid.uuid4(),
    correlation_id="corr-1",
)


def log(caplog, **kwargs) -> logging.LogRecord:
    with caplog.at_level(logging.INFO, logger="tool_gateway.audit"):
        audit_service.log_execution(
            tool_name="card.block", context=CONTEXT, risk_level="HIGH", **kwargs
        )
    assert len(caplog.records) == 1
    return caplog.records[0]


def test_held_for_confirmation_is_logged_as_awaiting_at_info(caplog):
    record = log(caplog, executed=False, success=False, error_code="CONFIRMATION_REQUIRED")
    assert record.levelno == logging.INFO
    assert record.getMessage() == "Tool awaiting confirmation: card.block"


@pytest.mark.parametrize("error_code", ["CONFIRMATION_INVALID", "TOOL_PROVIDER_UNAVAILABLE", None])
def test_real_failures_are_still_warnings(caplog, error_code):
    record = log(caplog, executed=True, success=False, error_code=error_code)
    assert record.levelno == logging.WARNING
    assert record.getMessage() == "Tool failed: card.block"


def test_success_is_logged_as_executed(caplog):
    record = log(caplog, executed=True, success=True)
    assert record.levelno == logging.INFO
    assert record.getMessage() == "Tool executed: card.block"
