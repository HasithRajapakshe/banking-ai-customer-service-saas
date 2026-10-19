"""The API Gateway signs the internal identity token for internal hops."""

import time
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from jose.exceptions import JWTError

from app.api.dependencies import get_current_active_user, get_current_user_roles, get_db
from app.core.config import settings
from app.core.internal_token import sign_internal_token
from app.models import AppUser, Role
from main import app

USER = AppUser(
    id=uuid.UUID("11111111-1111-4111-8111-111111111111"),
    tenant_id=uuid.UUID("22222222-2222-4222-8222-222222222222"),
    customer_id=uuid.UUID("33333333-3333-4333-8333-333333333333"),
    email="alice@example.com",
    status="active",
)


def decode(token: str) -> dict:
    return jwt.decode(
        token, settings.internal_jwt_secret, algorithms=["HS256"],
        audience=settings.internal_jwt_audience, issuer=settings.internal_jwt_issuer,
    )


def test_token_carries_identity_roles_and_conversation():
    conversation_id = uuid.uuid4()
    claims = decode(sign_internal_token(USER, ["CUSTOMER"], conversation_id=conversation_id))

    assert claims["sub"] == claims["user_id"] == str(USER.id)
    assert claims["tenant_id"] == str(USER.tenant_id)
    assert claims["customer_id"] == str(USER.customer_id)
    assert claims["roles"] == ["CUSTOMER"]
    assert claims["conversation_id"] == str(conversation_id)


def test_token_is_short_lived():
    claims = decode(sign_internal_token(USER, ["CUSTOMER"]))
    assert claims["exp"] - claims["iat"] == settings.internal_token_ttl_seconds == 60
    assert claims["exp"] <= int(time.time()) + 60


def test_token_secret_is_separate_from_user_jwt_secret():
    assert settings.internal_jwt_secret != settings.jwt_secret
    token = sign_internal_token(USER, ["CUSTOMER"])
    with pytest.raises(JWTError):
        jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], audience=settings.internal_jwt_audience)


def test_user_access_token_is_not_a_valid_internal_token():
    from app.core.security import create_access_token

    user_token = create_access_token({"sub": str(USER.id), "tenant_id": str(USER.tenant_id)})
    with pytest.raises(JWTError):
        decode(user_token)


@pytest.mark.asyncio(loop_scope="function")
async def test_chat_sends_a_token_for_the_user_and_conversation():
    async def user():
        return USER

    async def roles():
        return [Role(role_code="CUSTOMER", role_name="Customer", tenant_id=None)]

    session = AsyncMock()
    session.execute.return_value.scalar_one_or_none = lambda: None
    session.add = lambda obj: None
    app.dependency_overrides[get_current_active_user] = user
    app.dependency_overrides[get_current_user_roles] = roles
    app.dependency_overrides[get_db] = lambda: session

    conversation_id = uuid.uuid4()
    reply = {"message": "ok", "status": "completed", "intent": "greeting", "requires_confirmation": False}
    with patch("app.api.routes.chat.ai_agent_client.chat", new=AsyncMock(return_value=reply)) as agent:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/chat", json={"message": "hi", "conversation_id": str(conversation_id)})

    assert resp.status_code == 200
    claims = decode(agent.await_args.args[2])
    assert claims["user_id"] == str(USER.id)
    assert claims["customer_id"] == str(USER.customer_id)
    assert claims["conversation_id"] == str(conversation_id)
    assert claims["roles"] == ["CUSTOMER"]
