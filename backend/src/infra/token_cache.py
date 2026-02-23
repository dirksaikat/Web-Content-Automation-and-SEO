from src.infra.redis_client import get_redis
from redis.asyncio import Redis


class TokenCache:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.token_ttl = 2592000  # 30 days (match refresh token TTL)

    async def clear_user_access_token_blacklist(self, user_id: str) -> bool:
        key = f"blacklist:user_access:{user_id}"

        try:
            deleted = await self.redis.delete(key)
            if deleted:
                pass
                #log.info("cache.user_access_tokens.blacklist_cleared", user_id=user_id)
            return True
        except Exception as e:
            #log.error("cache.user_access_tokens.clear_error", user_id=user_id, error=str(e))
            return False

    async def revoke_all_user_tokens(self, user_id: str):
        key = f"user_tokens_revoked:{user_id}"
        try:
            # Set flag for 30 days
            await self.redis.setex(key, self.token_ttl, "1")
            #log.warning("cache.user_tokens.all_revoked", user_id=user_id)
        except Exception as e:
            pass
            #log.error("cache.user_tokens.revoke_error", user_id=user_id, error=str(e))

    async def revoke_token(self, token_hash: str, ttl: int | None = None):
        key = f"revoked_token:{token_hash}"
        ttl = ttl or self.token_ttl

        try:
            await self.redis.setex(key, ttl, "1")
            # todo log here
        except Exception as e:
            pass
            # todo log here

    async def blacklist_access_token(self, token_jti: str, ttl_seconds: int):
        """
        Blacklist an access token to prevent its use after logout.

        This enables immediate logout by preventing access token reuse.
        The token is stored until its natural expiration.

        Args:
            token_jti: JTI (unique ID) from the access token
            ttl_seconds: Time until token expires (from exp claim)
        """
        key = f"blacklist:access:{token_jti}"

        try:
            await self.redis.setex(key, ttl_seconds, "1")
            #log.info("cache.access_token.blacklisted", jti=token_jti[:8], ttl=ttl_seconds)
        except Exception as e:
            pass
            #log.error("cache.access_token.blacklist_error", jti=token_jti[:8], error=str(e))

    async def is_access_token_blacklisted(self, token_jti: str) -> bool:
        """
        Check if an access token is blacklisted.

        Args:
            token_jti: JTI (unique ID) from the access token

        Returns:
            True if token is blacklisted (logged out), False otherwise
        """
        key = f"blacklist:access:{token_jti}"

        try:
            exists = await self.redis.exists(key)

            if exists:
                pass
                #log.debug("cache.access_token.blacklisted_hit", jti=token_jti[:8])

            return exists > 0
        except Exception as e:
            #log.error("cache.access_token.blacklist_check_error", jti=token_jti[:8], error=str(e))
            # On error, assume not blacklisted (cautious approach)
            return False


_token_cache_instance: TokenCache | None = None


async def get_token_cache() -> TokenCache:

    global _token_cache_instance

    if _token_cache_instance is None:
        redis = await get_redis()
        _token_cache_instance = TokenCache(redis)

    return _token_cache_instance
