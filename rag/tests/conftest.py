import time
import uuid

import jwt

from app.core.config import settings

TENANT_A = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
USER_A = uuid.UUID("11111111-1111-4111-8111-111111111111")


def make_token(tenant_id=TENANT_A, user_id=USER_A, roles=("CUSTOMER",), expires_in=60, secret=None, **overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": settings.internal_jwt_issuer, "aud": settings.internal_jwt_audience,
        "sub": str(user_id), "iat": now, "exp": now + expires_in,
        "tenant_id": str(tenant_id) if tenant_id else None, "user_id": str(user_id),
        "customer_id": None, "roles": list(roles), **overrides,
    }
    return jwt.encode(claims, secret or settings.internal_jwt_secret, algorithm="HS256")


def auth(tenant_id=TENANT_A, **kwargs) -> dict:
    return {"X-Internal-Token": make_token(tenant_id=tenant_id, **kwargs)}
