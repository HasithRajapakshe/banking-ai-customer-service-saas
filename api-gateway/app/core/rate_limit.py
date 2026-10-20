import time
import uuid

import redis.asyncio as redis
from fastapi import Request

from app.core.config import settings
from app.core.security import decode_token

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

RATE_LIMIT_REQUESTS = 50
RATE_LIMIT_WINDOW = 60  # seconds


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Too Many Requests")


def rate_limit_key(request: Request) -> str:
    """Bucket per authenticated user (verified JWT "sub"), else per client IP.

    The token is signature-checked, so a forged token cannot select another
    user's bucket; an invalid token falls back to the IP bucket.
    """
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        payload = decode_token(auth.removeprefix("Bearer ").strip())
        if payload and payload.get("sub"):
            return f"rate_limit:user:{payload['sub']}"

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    return f"rate_limit:ip:{ip}"


async def check_rate_limit(request: Request) -> None:
    key = rate_limit_key(request)
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    async with redis_client.pipeline(transaction=True) as pipe:
        # Remove requests outside the sliding window
        pipe.zremrangebyscore(key, 0, window_start)
        # Count requests in window
        pipe.zcard(key)
        # Record this request; a unique member so concurrent requests
        # in the same second are all counted.
        pipe.zadd(key, {str(uuid.uuid4()): now})
        pipe.expire(key, RATE_LIMIT_WINDOW)
        results = await pipe.execute()

    request_count = results[1]
    if request_count >= RATE_LIMIT_REQUESTS:
        raise RateLimitExceeded(retry_after=RATE_LIMIT_WINDOW)
