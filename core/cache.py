import redis.asyncio as redis
from core.config import REDIS_URL

redis_pool = redis.ConnectionPool.from_url(
    REDIS_URL, decode_responses=True
)

async def get_redis():
    async with redis.Redis(connection_pool=redis_pool) as client:
        try:
            yield client
        finally:
            pass