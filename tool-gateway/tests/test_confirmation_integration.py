"""Integration tests for ConfirmationService against a live Redis (REDIS_URL)."""

import uuid

import pytest
import pytest_asyncio

from app.schemas.context import ToolExecutionContext
from app.services.confirmation_service import ConfirmationService

TOOL_NAME = "payment.create"
ARGUMENTS = {"amount": "100.00"}


def make_context(**overrides) -> ToolExecutionContext:
    values = {
        "tenant_id": uuid.uuid4(),
        "customer_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "conversation_id": uuid.uuid4(),
        "correlation_id": str(uuid.uuid4()),
    }
    values.update(overrides)
    return ToolExecutionContext(**values)


@pytest_asyncio.fixture
async def service():
    # A fresh client per test so it binds to the test's event loop.
    svc = ConfirmationService()
    yield svc
    await svc.redis_client.aclose()


@pytest.mark.asyncio(loop_scope="function")
async def test_redis_confirmation_flow(service):
    context = make_context()

    challenge_code = await service.create_challenge(TOOL_NAME, ARGUMENTS, context)
    assert isinstance(challenge_code, str)
    assert len(challenge_code) == 8

    verified = await service.verify_and_consume_challenge(challenge_code, context)
    assert verified is not None
    assert verified["tool_name"] == TOOL_NAME
    assert verified["arguments"] == ARGUMENTS

    # Replay must fail: the challenge was consumed.
    assert await service.verify_and_consume_challenge(challenge_code, context) is None


@pytest.mark.asyncio(loop_scope="function")
async def test_redis_confirmation_wrong_user(service):
    context = make_context()
    challenge_code = await service.create_challenge(TOOL_NAME, ARGUMENTS, context)

    other_user = context.model_copy(update={"user_id": uuid.uuid4()})
    assert await service.verify_and_consume_challenge(challenge_code, other_user) is None


@pytest.mark.asyncio(loop_scope="function")
async def test_redis_confirmation_wrong_tenant(service):
    context = make_context()
    challenge_code = await service.create_challenge(TOOL_NAME, ARGUMENTS, context)

    other_tenant = context.model_copy(update={"tenant_id": uuid.uuid4()})
    assert await service.verify_and_consume_challenge(challenge_code, other_tenant) is None


@pytest.mark.asyncio(loop_scope="function")
async def test_redis_confirmation_wrong_code(service):
    context = make_context()
    await service.create_challenge(TOOL_NAME, ARGUMENTS, context)

    assert await service.verify_and_consume_challenge("invalid-code", context) is None
