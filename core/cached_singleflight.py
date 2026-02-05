# core/cached_singleflight.py

import json
from typing import Awaitable, Callable, Optional

from core.redis_lock import singleflight

USE_DISTRIBUTED_LOCK = False

async def cached_singleflight_str(
    *,
    redis,
    cache_key: str,
    ttl: int,
    lock_key: str,
    lock_ttl: int,
    wait_timeout: float,
    poll_interval: float,
    create: Callable[[], Awaitable[str]],
    fallback: Optional[Callable[[], Awaitable[Optional[str]]]] = None,
) -> str:
    async def cache_get():
        return await redis.get(cache_key)

    async def cache_set(val: str):
        await redis.set(cache_key, val, ex=ttl)

    
    if not USE_DISTRIBUTED_LOCK:
        cached = await cache_get()
        if cached is not None:
            return cached
        try:
            result = await create()
        except Exception:
            if fallback is not None:
                fb = await fallback()
                if fb is not None:
                    await cache_set(fb)
                    return fb
            raise
        await cache_set(result)
        return result


    result = await singleflight(
        redis=redis,
        cache_get=cache_get,
        cache_set=cache_set,
        create=create,
        lock_key=lock_key,
        lock_ttl=lock_ttl,
        wait_timeout=wait_timeout,
        poll_interval=poll_interval,
        fallback=fallback,
    )
    # fallback로 얻은 값도 캐시에 올려두기
    await cache_set(result)
    return result


async def cached_singleflight_json(
    *,
    redis,
    cache_key: str,
    ttl: int,
    lock_key: str,
    lock_ttl: int,
    wait_timeout: float,
    poll_interval: float,
    create: Callable[[], Awaitable[dict]],
    fallback: Optional[Callable[[], Awaitable[Optional[dict]]]] = None,
) -> dict:
    async def cache_get():
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
        return None

    async def cache_set(val: dict):
        await redis.set(cache_key, json.dumps(val), ex=ttl)

    if not USE_DISTRIBUTED_LOCK:
        cached = await cache_get()
        if cached is not None:
            return cached
        try:
            result = await create()
        except Exception:
            if fallback is not None:
                fb = await fallback()
                if fb is not None:
                    await cache_set(fb)
                    return fb
            raise
        await cache_set(result)
        return result

    result = await singleflight(
        redis=redis,
        cache_get=cache_get,
        cache_set=cache_set,
        create=create,
        lock_key=lock_key,
        lock_ttl=lock_ttl,
        wait_timeout=wait_timeout,
        poll_interval=poll_interval,
        fallback=fallback,
    )
    # fallback로 얻은 값도 캐시에 올려두기
    await cache_set(result)
    return result
