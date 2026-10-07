import time
import redis.asyncio as redis
from fastapi import Request, HTTPException
from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

RATE_LIMIT_REQUESTS = 50
RATE_LIMIT_WINDOW = 60 # seconds

async def check_rate_limit(request: Request):
    # Use client IP or token subject as the key
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0] if forwarded else request.client.host
    
    auth = request.headers.get("authorization")
    key = f"rate_limit:{ip}"
    if auth and auth.startswith("Bearer "):
        key = f"rate_limit:token:{auth.split(' ')[1][:10]}"

    current = int(time.time())
    window_start = current - RATE_LIMIT_WINDOW
    
    async with redis_client.pipeline(transaction=True) as pipe:
        # Remove old requests
        await pipe.zremrangebyscore(key, 0, window_start)
        # Count requests in window
        await pipe.zcard(key)
        # Add current request
        await pipe.zadd(key, {str(current): current})
        # Set expiry to window size
        await pipe.expire(key, RATE_LIMIT_WINDOW)
        
        results = await pipe.execute()
        
    request_count = results[1]
    if request_count >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests. Please try again later."
        )
