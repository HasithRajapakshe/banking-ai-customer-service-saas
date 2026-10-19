"""Verify the internal identity token signed by the API Gateway.

The token is the ONLY source of who is calling: tenant, customer, user,
roles and conversation. It is short-lived (seconds), signed with a secret
separate from the user JWT secret, and scoped by issuer and audience.

Missing, expired, malformed or tampered tokens -> 401. Identity fields in a
request that disagree with the token -> 403 (checked by the route).
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
    customer_id: uuid.UUID | None
    user_id: uuid.UUID
    roles: tuple[str, ...]
    conversation_id: uuid.UUID | None


def _unauthorized(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=401, detail={"code": code, "message": message})


def _optional_uuid(value) -> uuid.UUID | None:
    return uuid.UUID(str(value)) if value else None


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
        if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
            raise ValueError("roles must be a list of strings")
        return InternalIdentity(
            tenant_id=uuid.UUID(str(claims["tenant_id"])),
            customer_id=_optional_uuid(claims.get("customer_id")),
            user_id=user_id,
            roles=tuple(roles),
            conversation_id=_optional_uuid(claims.get("conversation_id")),
        )
    except (ValueError, TypeError) as exc:
        raise _unauthorized("INTERNAL_TOKEN_INVALID", f"Internal identity token claims are invalid: {exc}")


async def require_internal_identity(
    x_internal_token: str | None = Header(default=None, alias=INTERNAL_TOKEN_HEADER),
) -> InternalIdentity:
    if not x_internal_token:
        raise _unauthorized("INTERNAL_TOKEN_REQUIRED", "Internal identity token is required.")
    return decode_internal_token(x_internal_token)


def identity_mismatch(field: str) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": "IDENTITY_MISMATCH", "message": f"{field} does not match the authenticated identity."},
    )
