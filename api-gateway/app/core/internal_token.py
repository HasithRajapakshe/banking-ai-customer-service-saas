"""Sign the short-lived internal identity token sent to internal services.

The token carries who is acting (tenant, customer, user, roles, conversation)
from the authenticated user session; tool-gateway and rag take identity ONLY
from it. It is valid for `internal_token_ttl_seconds` (default 60 s) and
signed with `internal_jwt_secret`, which is separate from the user JWT secret.
"""

import time
import uuid

from jose import jwt

from app.core.config import settings
from app.models import AppUser

INTERNAL_TOKEN_HEADER = "X-Internal-Token"


def sign_internal_token(
    user: AppUser,
    roles: list[str],
    conversation_id: uuid.UUID | None = None,
) -> str:
    now = int(time.time())
    claims = {
        "iss": settings.internal_jwt_issuer,
        "aud": settings.internal_jwt_audience,
        "sub": str(user.id),
        "iat": now,
        "exp": now + settings.internal_token_ttl_seconds,
        "jti": str(uuid.uuid4()),
        "tenant_id": str(user.tenant_id),
        "customer_id": str(user.customer_id) if user.customer_id else None,
        "user_id": str(user.id),
        "roles": sorted(set(roles)),
        "conversation_id": str(conversation_id) if conversation_id else None,
    }
    return jwt.encode(claims, settings.internal_jwt_secret, algorithm="HS256")


def internal_headers(token: str, correlation_id: str) -> dict[str, str]:
    return {INTERNAL_TOKEN_HEADER: token, "X-Correlation-ID": correlation_id}
