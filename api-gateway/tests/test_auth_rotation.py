import pytest
import uuid
import json
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.security import create_refresh_token

@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")

@pytest.mark.asyncio(loop_scope="function")
@patch("app.api.routes.auth.redis_client.get")
@patch("app.api.routes.auth.redis_client.delete")
@patch("app.api.routes.auth.redis_client.set")
async def test_refresh_token_rotation(mock_set, mock_delete, mock_get, client):
    # Mock redis session
    jti = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    mock_get.return_value = json.dumps({"user_id": user_id, "status": "active"})
    
    # Mock DB
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    
    from app.models import AppUser
    mock_user = AppUser(
        id=uuid.UUID(user_id),
        tenant_id=uuid.uuid4(),
        status="active"
    )
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    from app.core.database import get_db
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Create valid refresh token
    refresh_token = create_refresh_token(data={"sub": user_id, "jti": jti})
    
    client.cookies.set("refresh_token", refresh_token)
    
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 200
    
    data = resp.json()
    assert "access_token" in data
    assert data["refresh_token"] == "hidden"
    
    # Assert old token was deleted
    mock_delete.assert_called_with(f"refresh_session:{jti}")
    # Assert new token was set
    assert mock_set.called

@pytest.mark.asyncio(loop_scope="function")
@patch("app.api.routes.auth.redis_client.get")
async def test_refresh_token_revoked(mock_get, client):
    jti = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    # Mock redis session as revoked
    mock_get.return_value = json.dumps({"user_id": user_id, "status": "revoked"})
    
    refresh_token = create_refresh_token(data={"sub": user_id, "jti": jti})
    client.cookies.set("refresh_token", refresh_token)
    
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401
    assert "Session revoked" in resp.json()["detail"]
