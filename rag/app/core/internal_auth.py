"""Verify the internal identity token signed by the API Gateway.

The tenant is taken ONLY from the token. A tenant_id sent in a query or form
must match it (403 otherwise). Missing, expired, malformed or tampered
tokens -> 401.
"""

import uuid
from dataclasses import dataclass

import jwt
from fastapi import Header, HTTPException

from app.core.config import settings

INTERNAL_TOKEN_HEADER = "X-Internal-Token"


@dataclass(frozen=True)
class InternalIdentity:
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    customer_id: uuid.UUID | None
    roles: tuple[str, ...]


def _unauthorized(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=401, detail={"code": code, "message": message})


def decode_internal_token(token: str) -> InternalIdentity:
    try:
        claims = jwt.decode(
            token,
            settings.internal_jwt_secret,
            algorithms=["HS256"],
            audience=settings.internal_jwt_audience,
            issuer=settings.internal_jwt_issuer,
            leeway=settings.internal_jwt_leeway_seconds,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "tenant_id", "user_id"]},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("INTERNAL_TOKEN_EXPIRED", "Internal identity token has expired.")
    except jwt.InvalidTokenError as exc:
        raise _unauthorized("INTERNAL_TOKEN_INVALID", f"Internal identity token is invalid: {exc}")

    try:
        user_id = uuid.UUID(str(claims["user_id"]))
        if str(user_id) != str(claims["sub"]):
            raise ValueError("sub does not match user_id")
        roles = claims.get("roles") or []
        if not isinstance(roles, list):
            raise ValueError("roles must be a list")
        customer = claims.get("customer_id")
        return InternalIdentity(
            tenant_id=uuid.UUID(str(claims["tenant_id"])),
            user_id=user_id,
            customer_id=uuid.UUID(str(customer)) if customer else None,
            roles=tuple(str(r) for r in roles),
        )
    except (ValueError, TypeError) as exc:
        raise _unauthorized("INTERNAL_TOKEN_INVALID", f"Internal identity token claims are invalid: {exc}")


async def require_internal_identity(
    x_internal_token: str | None = Header(default=None, alias=INTERNAL_TOKEN_HEADER),
) -> InternalIdentity:
    if not x_internal_token:
        raise _unauthorized("INTERNAL_TOKEN_REQUIRED", "Internal identity token is required.")
    return decode_internal_token(x_internal_token)


def tenant_from_token(identity: InternalIdentity, sent_tenant_id: uuid.UUID | None) -> uuid.UUID:
    if sent_tenant_id is not None and sent_tenant_id != identity.tenant_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "IDENTITY_MISMATCH", "message": "tenant_id does not match the authenticated identity."},
        )
    return identity.tenant_id
