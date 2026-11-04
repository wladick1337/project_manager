from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.redis import get_redis


class RateLimiter:
    def __init__(self, times: int = 5, seconds: int = 60):
        self.times = times
        self.seconds = seconds

    async def __call__(
        self,
        request: Request,
        redis: Redis = Depends(get_redis),
    ) -> None:
        client_ip = request.client.host if request.client else "127.0.0.1"
        endpoint = request.url.path
        key = f"rate_limit:{endpoint}:{client_ip}"

        current_requests = await redis.incr(key)

        if current_requests == 1:
            await redis.expire(key, self.seconds)

        elif await redis.ttl(key) == -1:
            await redis.expire(key, self.seconds)

        if current_requests > self.times:
            ttl = await redis.ttl(key)
            retry_after = str(max(ttl, 1))

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": retry_after},
            )
