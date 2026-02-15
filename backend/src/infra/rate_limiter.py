import time
from fastapi import Request

from enum import Enum
from src.infra.redis_client import get_redis
from src.features.auth.auth_error import AuthError


class RateLimitKey(Enum):
    IP = "ip"
    IP_ENDPOINT = "ip_endpoint"
    IP_USERNAME = "ip_username"
    GLOBAL = "global"


class RateLimiter:
    def __init__(
            self,
            *,
            limit: int,
            window_seconds: int,
            key_type: RateLimitKey,
            block_seconds: int,
            prefix: str = "rate_limit",
    ):
        self.limit = limit
        self.window = window_seconds
        self.key_type = key_type
        self.prefix = prefix
        self.block_seconds = block_seconds

    async def __call__(self, request: Request):
        redis = await get_redis()
        identifier = await self._build_key(request)

        rate_key = f"{self.prefix}:{identifier}"
        block_key = f"{self.prefix}:block:{identifier}"

        # 1️⃣ Check if blocked
        if await redis.exists(block_key):
            raise AuthError.rate_limited()

        # 2️⃣ Sliding window logic
        now = int(time.time())

        pipe = redis.pipeline()
        await pipe.zadd(rate_key, {now: now})
        await pipe.zremrangebyscore(rate_key, 0, now - self.window)
        await pipe.zcard(rate_key)
        await pipe.expire(rate_key, self.window)

        _, _, count, _ = await pipe.execute()

        if count > self.limit:
            if self.block_seconds:
                await redis.set(block_key, "1", ex=self.block_seconds)

            raise AuthError.rate_limited()

    async def _build_key(self, request: Request) -> str:
        match self.key_type:
            case RateLimitKey.IP:
                return self._ip_key(request)

            case RateLimitKey.IP_ENDPOINT:
                return self._ip_endpoint_key(request)

            case RateLimitKey.IP_USERNAME:
                return await self._ip_username_key(request)

            case RateLimitKey.GLOBAL:
                return "global"

            case _:
                raise RuntimeError("Invalid rate limit key type")

    # ---------- key implementations ----------

    def _ip_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        return forwarded.split(",")[0] if forwarded else request.client.host

    def _ip_endpoint_key(self, request: Request) -> str:
        ip = self._ip_key(request)
        return f"{ip}:{request.url.path}"

    async def _ip_username_key(self, request: Request) -> str:
        body = await request.json()
        username = body.get("username", "anonymous")
        ip = self._ip_key(request)
        return f"{ip}:{username}"


def get_rate_limiter(
        limit: int,
        window_seconds: int,
        key_type: RateLimitKey,
        block_seconds=3600,
        prefix: str = "rate_limit",
) -> RateLimiter:
    return RateLimiter(
        limit=limit,
        window_seconds=window_seconds,
        key_type=key_type,
        block_seconds=block_seconds,
        prefix=prefix
    )
