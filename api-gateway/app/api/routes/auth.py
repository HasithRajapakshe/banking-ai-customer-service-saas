from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json

from app.api.dependencies import get_current_user, get_current_active_user, get_current_user_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, verify_password, decode_token
from app.models import AppUser, Role
from app.schemas.auth import LoginRequest, Token, UserResponse
from app.core.rate_limit import redis_client

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AppUser).where(AppUser.email == login_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token_payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "customer_id": str(user.customer_id) if user.customer_id else None,
    }
    access_token = create_access_token(data=access_token_payload)
    
    jti = str(uuid.uuid4())
    refresh_token = create_refresh_token(data={"sub": str(user.id), "jti": jti})

    # Store in Redis
    session_data = {"user_id": str(user.id), "status": "active"}
    await redis_client.set(f"refresh_session:{jti}", json.dumps(session_data), ex=7 * 24 * 60 * 60)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return Token(
        access_token=access_token,
        refresh_token="hidden", # Do not expose in JSON
        token_type="bearer",
    )

@router.post("/refresh", response_model=Token)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    user_id_str = payload.get("sub")
    jti = payload.get("jti")
    
    if not jti:
        raise HTTPException(status_code=401, detail="Invalid refresh token format")
        
    session_raw = await redis_client.get(f"refresh_session:{jti}")
    if not session_raw:
        # Potential replay attack if someone uses an old token, we could revoke all tokens for user.
        raise HTTPException(status_code=401, detail="Session expired or revoked")
        
    session_data = json.loads(session_raw)
    if session_data.get("status") != "active":
        raise HTTPException(status_code=401, detail="Session revoked")
        
    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user id in token")
        
    stmt = select(AppUser).where(AppUser.id == user_uuid, AppUser.status == "active")
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Invalidate old token
    await redis_client.delete(f"refresh_session:{jti}")

    # Issue new tokens
    access_token_payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "customer_id": str(user.customer_id) if user.customer_id else None,
    }
    new_access_token = create_access_token(data=access_token_payload)
    
    new_jti = str(uuid.uuid4())
    new_refresh_token = create_refresh_token(data={"sub": str(user.id), "jti": new_jti})
    
    new_session_data = {"user_id": str(user.id), "status": "active"}
    await redis_client.set(f"refresh_session:{new_jti}", json.dumps(new_session_data), ex=7 * 24 * 60 * 60)
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    return Token(
        access_token=new_access_token,
        refresh_token="hidden",
        token_type="bearer",
    )

@router.post("/logout")
async def logout(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        payload = decode_token(refresh_token)
        if payload:
            jti = payload.get("jti")
            if jti:
                await redis_client.delete(f"refresh_session:{jti}")
                
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: AppUser = Depends(get_current_active_user),
):
    return current_user

@router.get("/me/roles", response_model=list[str])
async def read_user_roles(
    roles: list[Role] = Depends(get_current_user_roles),
):
    return [role.role_code for role in roles]
