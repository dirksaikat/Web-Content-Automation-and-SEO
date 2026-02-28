from .rate_limit_config import RateLimitConfig, RATE_LIMITS, RateLimitKey
import time
from fastapi import Request
from .redis_client import get_redis


class RateLimiter:
    def __init__(self, redis, config: dict[str, RateLimitConfig], prefix="rate_limit"):
        self.redis = redis
        self.config = config
        self.prefix = prefix

    async def is_rate_limited(
            self,
            scope: str,
            request: Request,
            identifier: str | None = None
    ) -> bool:
        if scope not in self.config:
            raise RuntimeError(f"Rate limit scope '{scope}' not configured")

        cfg = self.config[scope]

        if identifier is None:
            identifier = await self._build_key(request, cfg.key_type)

        rate_key = f"{self.prefix}:{scope}:{identifier}"
        block_key = f"{self.prefix}:{scope}:block:{identifier}"

        if await self.redis.exists(block_key):
            return True

        now = int(time.time())

        pipe = self.redis.pipeline()
        await pipe.zadd(rate_key, {now: now})
        await pipe.zremrangebyscore(rate_key, 0, now - cfg.window_seconds)
        await pipe.zcard(rate_key)
        await pipe.expire(rate_key, cfg.window_seconds)

        _, _, count, _ = await pipe.execute()

        if count > cfg.limit:
            if cfg.block_seconds:
                await self.redis.set(block_key, "1", ex=cfg.block_seconds)
            return True

        return False

    # ---------------------------------
    # 🔑 Key builder
    # ---------------------------------

    async def _build_key(self, request: Request, key_type: RateLimitKey) -> str:
        match key_type:
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
        username = body.get("username", "email")
        ip = self._ip_key(request)
        return f"{ip}:{username}"


_rate_limiter: RateLimiter | None = None


async def get_rate_limiter() -> RateLimiter:
    global _rate_limiter

    if _rate_limiter is None:
        redis = await get_redis()
        _rate_limiter = RateLimiter(
            redis=redis,
            config=RATE_LIMITS,
        )

    return _rate_limiter
