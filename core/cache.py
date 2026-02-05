# core/cache.py

import redis.asyncio as redis
from core.config import REDIS_URL

redis_pool = redis.ConnectionPool.from_url(
    REDIS_URL, decode_responses=True
)

# 전역 client 재사용
redis_client = redis.Redis(connection_pool=redis_pool)

async def get_redis():
    yield redis_client
