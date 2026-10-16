import uuid

import pytest

from app.tools.registry import register_default_tools, tool_registry


# =========================
# Known test IDs
# =========================

TEST_TENANT_ID = uuid.UUID("f498100f-80c4-467e-84ec-ebfe5470b442")
TEST_CUSTOMER_ID = uuid.UUID("5f695079-da87-45a2-8a9c-b778600b2c32")
TEST_ACCOUNT_ID = uuid.UUID("4ba945f9-df1a-473a-bca7-3e397029cb29")
TEST_CARD_ID = uuid.uuid4()
TEST_PAYMENT_ID = uuid.uuid4()
TEST_BENEFICIARY_ID = uuid.uuid4()
TEST_LOAN_ID = uuid.uuid4()
TEST_COMPLAINT_ID = uuid.uuid4()


def make_execute_payload(
    tool_name: str,
    arguments: dict | None = None,
    confirmed: bool = False,
    challenge_code: str | None = None,
    tenant_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
) -> dict:
    return {
        "tool_name": tool_name,
        "tenant_id": str(tenant_id or TEST_TENANT_ID),
        "customer_id": str(customer_id or TEST_CUSTOMER_ID),
        "arguments": arguments or {},
        "confirmed": confirmed,
        "challenge_code": challenge_code,
    }


# Ensure tools are registered for all tests
register_default_tools()
@pytest.fixture(autouse=True)
def mock_confirmation_service(monkeypatch):
    async def mock_create_challenge(*args, **kwargs):
        return "TEST_CHALLENGE_CODE"

    monkeypatch.setattr('app.services.tool_gateway_service.confirmation_service.create_challenge', mock_create_challenge)
    
    # We don't globally mock verify_and_consume_challenge; it's patched individually where needed.
