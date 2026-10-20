import secrets

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_internal_api_key(
    x_internal_api_key: str | None = Header(
        default=None,
        alias="X-Internal-API-Key",
    ),
) -> None:
    if not x_internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_INTERNAL_API_KEY",
                "message": "Internal API key is required.",
            },
        )

    if not secrets.compare_digest(
        x_internal_api_key,
        settings.internal_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INVALID_INTERNAL_API_KEY",
                "message": "Invalid internal API key.",
            },
        )