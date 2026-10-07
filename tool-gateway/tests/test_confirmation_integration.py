import pytest
import uuid
from app.services.confirmation_service import ConfirmationService

# Real instance for integration tests
real_confirmation_service = ConfirmationService()

@pytest.mark.asyncio(loop_scope="function")
async def test_redis_confirmation_flow():
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conversation_id = uuid.uuid4()
    tool_name = "payment.create"
    arguments = {"amount": "100.00"}

    # 1. Create challenge
    challenge = await real_confirmation_service.create_challenge(
        tenant_id=tenant_id,
        customer_id=customer_id,
        user_id=user_id,
        conversation_id=conversation_id,
        tool_name=tool_name,
        arguments=arguments,
        risk_level="HIGH"
    )

    assert challenge is not None
    assert challenge.challenge_code is not None
    
    # 2. Redis key exists (implicitly tested if verify succeeds)
    
    # 3. Correct user confirm -> operation succeeds
    verified = await real_confirmation_service.verify_and_consume_challenge(
        tenant_id=tenant_id,
        customer_id=customer_id,
        user_id=user_id,
        conversation_id=conversation_id,
        challenge_code=challenge.challenge_code
    )
    
    assert verified is not None
    assert verified["tool_name"] == tool_name
    assert verified["arguments"] == arguments
    
    # 4. Second confirmation -> fails (already consumed)
    verified_second = await real_confirmation_service.verify_and_consume_challenge(
        tenant_id=tenant_id,
        customer_id=customer_id,
        user_id=user_id,
        conversation_id=conversation_id,
        challenge_code=challenge.challenge_code
    )
    assert verified_second is None
    
@pytest.mark.asyncio(loop_scope="function")
async def test_redis_confirmation_wrong_user():
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conversation_id = uuid.uuid4()
    tool_name = "payment.create"
    arguments = {"amount": "100.00"}

    challenge = await real_confirmation_service.create_challenge(
        tenant_id=tenant_id,
        customer_id=customer_id,
        user_id=user_id,
        conversation_id=conversation_id,
        tool_name=tool_name,
        arguments=arguments,
        risk_level="HIGH"
    )

    # Wrong user ID
    verified = await real_confirmation_service.verify_and_consume_challenge(
        tenant_id=tenant_id,
        customer_id=customer_id,
        user_id=uuid.uuid4(),
        conversation_id=conversation_id,
        challenge_code=challenge.challenge_code
    )
    assert verified is None

@pytest.mark.asyncio(loop_scope="function")
async def test_redis_confirmation_wrong_tenant():
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conversation_id = uuid.uuid4()
    tool_name = "payment.create"
    arguments = {"amount": "100.00"}

    challenge = await real_confirmation_service.create_challenge(
        tenant_id=tenant_id,
        customer_id=customer_id,
        user_id=user_id,
        conversation_id=conversation_id,
        tool_name=tool_name,
        arguments=arguments,
        risk_level="HIGH"
    )

    # Wrong tenant ID
    verified = await real_confirmation_service.verify_and_consume_challenge(
        tenant_id=uuid.uuid4(),
        customer_id=customer_id,
        user_id=user_id,
        conversation_id=conversation_id,
        challenge_code=challenge.challenge_code
    )
    assert verified is None

@pytest.mark.asyncio(loop_scope="function")
async def test_redis_confirmation_wrong_code():
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conversation_id = uuid.uuid4()
    tool_name = "payment.create"
    arguments = {"amount": "100.00"}

    await real_confirmation_service.create_challenge(
        tenant_id=tenant_id,
        customer_id=customer_id,
        user_id=user_id,
        conversation_id=conversation_id,
        tool_name=tool_name,
        arguments=arguments,
        risk_level="HIGH"
    )

    # Unknown code
    verified = await real_confirmation_service.verify_and_consume_challenge(
        tenant_id=tenant_id,
        customer_id=customer_id,
        user_id=user_id,
        conversation_id=conversation_id,
        challenge_code="invalid-code"
    )
    assert verified is None
