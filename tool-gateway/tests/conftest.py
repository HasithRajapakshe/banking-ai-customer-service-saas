import time
import uuid

import jwt
import pytest
from fastapi import Request

from app.core.config import settings
from app.core.internal_auth import InternalIdentity, require_internal_identity
from app.tools.registry import register_default_tools, tool_registry
from main import app


# =========================
# Known test IDs
# =========================

TEST_TENANT_ID = uuid.UUID("f498100f-80c4-467e-84ec-ebfe5470b442")
TEST_CUSTOMER_ID = uuid.UUID("5f695079-da87-45a2-8a9c-b778600b2c32")
TEST_ACCOUNT_ID = uuid.UUID("4ba945f9-df1a-473a-bca7-3e397029cb29")
TEST_USER_ID = uuid.UUID("0c1e2d3f-4a5b-4c6d-8e7f-9a0b1c2d3e4f")
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
    user_id: uuid.UUID | None = TEST_USER_ID,
) -> dict:
    return {
        "tool_name": tool_name,
        "tenant_id": str(tenant_id or TEST_TENANT_ID),
        "customer_id": str(customer_id or TEST_CUSTOMER_ID),
        "user_id": str(user_id) if user_id else None,
        "arguments": arguments or {},
        "confirmed": confirmed,
        "challenge_code": challenge_code,
    }


def make_token(
    *,
    tenant_id=TEST_TENANT_ID,
    customer_id=TEST_CUSTOMER_ID,
    user_id=TEST_USER_ID,
    roles=("CUSTOMER",),
    conversation_id=None,
    expires_in: int = 60,
    secret: str | None = None,
    **overrides,
) -> str:
    """An internal identity token as the API Gateway signs it."""
    now = int(time.time())
    claims = {
        "iss": settings.internal_jwt_issuer,
        "aud": settings.internal_jwt_audience,
        "sub": str(user_id),
        "iat": now,
        "exp": now + expires_in,
        "tenant_id": str(tenant_id),
        "customer_id": str(customer_id) if customer_id else None,
        "user_id": str(user_id),
        "roles": list(roles),
        "conversation_id": str(conversation_id) if conversation_id else None,
        **overrides,
    }
    return jwt.encode(claims, secret or settings.internal_jwt_secret, algorithm="HS256")


# Ensure tools are registered for all tests
register_default_tools()

# Role -> permissions as granted by Alembic revision 0002: customers get every
# tool permission; support agents get none of the high-risk ones.
CUSTOMER_PERMISSIONS = frozenset(tool.permission for tool in tool_registry.all())
HIGH_RISK_PERMISSIONS = frozenset(tool.permission for tool in tool_registry.all() if tool.requires_confirmation)
ROLE_PERMISSIONS = {
    "CUSTOMER": CUSTOMER_PERMISSIONS,
    "SUPPORT_AGENT": CUSTOMER_PERMISSIONS - HIGH_RISK_PERMISSIONS,
    "ADMIN": frozenset({"knowledge.manage", "audit.read", "users.manage"}),
}


@pytest.fixture(autouse=True)
def mock_confirmation_service(monkeypatch):
    async def mock_create_challenge(*args, **kwargs):
        return "TEST_CHALLENGE_CODE"

    monkeypatch.setattr('app.services.tool_gateway_service.confirmation_service.create_challenge', mock_create_challenge)

    # We don't globally mock verify_and_consume_challenge; it's patched individually where needed.


@pytest.fixture(autouse=True)
def role_permissions(monkeypatch):
    """Permission lookups without a database."""

    async def permissions_for_roles(roles):
        return frozenset().union(*(ROLE_PERMISSIONS.get(r, frozenset()) for r in roles))

    monkeypatch.setattr(
        "app.services.authorization_service.permission_repository.permissions_for_roles", permissions_for_roles
    )


@pytest.fixture(autouse=True)
def audit_records(monkeypatch) -> list:
    """Captures what would be written to tool_execution/audit_log."""
    records = []

    async def record(entry):
        records.append(entry)
        return uuid.uuid4()

    monkeypatch.setattr("app.services.audit_service.audit_repository.record", record)
    return records


@pytest.fixture(autouse=True)
def identity_from_body():
    """Most tests exercise tool logic, not authentication: derive a trusted
    CUSTOMER identity from the request body. test_internal_auth.py removes
    this override to test the real token check."""

    async def identity(request: Request) -> InternalIdentity:
        body = await request.json()
        return InternalIdentity(
            tenant_id=uuid.UUID(body["tenant_id"]),
            customer_id=uuid.UUID(body["customer_id"]),
            user_id=uuid.UUID(body["user_id"]) if body.get("user_id") else TEST_USER_ID,
            roles=("CUSTOMER",),
            conversation_id=None,
        )

    app.dependency_overrides[require_internal_identity] = identity
    yield
    app.dependency_overrides.pop(require_internal_identity, None)
