import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from main import app

# Mock dependencies
async def override_get_current_active_user():
    from app.models import AppUser
    return AppUser(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        tenant_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        customer_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        status="active"
    )

async def override_get_db():
    mock_session = AsyncMock()
    yield mock_session


from app.api.dependencies import get_current_active_user, get_db

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.fixture
def client(mock_db_session):
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[get_db] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")

@pytest.mark.asyncio(loop_scope="function")
async def test_get_messages_idor(client, mock_db_session):
    from app.models import Conversation
    # Create a conversation belonging to someone else
    conv = Conversation(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID("44444444-4444-4444-4444-444444444444"), # Different tenant
        customer_id=uuid.UUID("55555555-5555-5555-5555-555555555555") # Different customer
    )
    
    # Mock db to return None (meaning it was filtered out by the WHERE clause in our code)
    # The code does: stmt = select(Conversation).where(Conversation.tenant_id == current_user.tenant_id, Conversation.customer_id == current_user.customer_id)
    # So if the DB returns None, our app returns 404
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    resp = await client.get(f"/api/v1/chat/conversations/{conv.id}/messages")
    assert resp.status_code == 404

@pytest.mark.asyncio(loop_scope="function")
async def test_chat_with_agent_idor(client, mock_db_session):
    from app.models import Conversation
    # Chat with a conversation ID belonging to Bob
    conv_id = uuid.uuid4()
    conv = Conversation(
        id=conv_id,
        tenant_id=uuid.UUID("22222222-2222-2222-2222-222222222222"), # Same tenant
        customer_id=uuid.UUID("55555555-5555-5555-5555-555555555555") # Different customer
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = conv
    mock_db_session.execute.return_value = mock_result
    
    payload = {
        "message": "Hello",
        "conversation_id": str(conv_id)
    }
    
    resp = await client.post("/api/v1/chat", json=payload)
    assert resp.status_code == 403
    assert "Not authorized" in resp.json()["detail"]
