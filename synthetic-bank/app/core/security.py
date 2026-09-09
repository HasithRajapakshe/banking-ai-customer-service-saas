import secrets

from fastapi import Header

from app.core.config import settings
from app.core.errors import AppError


INTERNAL_API_KEY_HEADER = "X-Internal-API-Key"


async def require_internal_api_key(
    x_internal_api_key: str | None = Header(
        default=None,
        alias=INTERNAL_API_KEY_HEADER,
    ),
) -> None:

    if not x_internal_api_key:
        raise AppError(
            status_code=401,
            code="INTERNAL_AUTH_REQUIRED",
            message="Internal API key is required",
        )

    if not secrets.compare_digest(
        x_internal_api_key,
        settings.internal_api_key,
    ):
        raise AppError(
            status_code=401,
            code="INVALID_INTERNAL_API_KEY",
            message="Invalid internal API key",
        )