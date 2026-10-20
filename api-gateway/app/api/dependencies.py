import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models import AppUser, Role, UserRole, RolePermission, Permission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> AppUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str | None = payload.get("sub")
    token_type: str | None = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception

    stmt = select(AppUser).where(AppUser.id == user_uuid, AppUser.status == "active")
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user

async def get_current_active_user(
    current_user: AppUser = Depends(get_current_user),
) -> AppUser:
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_roles(
    current_user: AppUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> list[Role]:
    stmt = (
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

def require_permission(required_permission: str):
    """Dependency factory for RBAC verification."""
    async def permission_checker(
        current_user: AppUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> AppUser:
        # Check if the user has the required permission through their roles
        stmt = (
            select(Permission.permission_code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        user_permissions = [row for row in result.scalars().all()]
        
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {required_permission}"
            )
        return current_user
        
    return permission_checker

async def require_customer_context(
    customer_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_active_user)
) -> AppUser:
    """Ensure the user is authorized to act on behalf of the customer."""
    # If the user is a normal customer, they can only access their own customer_id
    # We should really check if they have a generic 'support' role, but for now:
    if current_user.customer_id is not None and current_user.customer_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this customer's data"
        )
    return current_user
