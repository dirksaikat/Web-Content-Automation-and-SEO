from redis.asyncio import ConnectionPool, Redis
from src.core.config.settings import Config

_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None


async def get_redis() -> Redis:
    global _redis_client, _redis_pool

    if _redis_client is None:
        _redis_pool = ConnectionPool.from_url(Config.REDIS_URL, decode_responses=True, max_connections=20)
        _redis_client = Redis(connection_pool=_redis_pool)
        #todo log here...
    return _redis_client


async def close_redis():
    global _redis_client, _redis_pool

    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        #todo log redis closed

    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
        #todo log pool disconnedted