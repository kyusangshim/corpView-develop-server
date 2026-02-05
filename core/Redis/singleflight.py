# core/redis_lock.py

import asyncio
from typing import Awaitable, Callable, Optional, TypeVar

T = TypeVar("T")


class SingleFlightTimeout(Exception):
    """락 대기 중 타임아웃"""


async def singleflight(
    *,
    redis,
    cache_get: Callable[[], Awaitable[Optional[T]]],
    cache_set: Callable[[T], Awaitable[None]],
    create: Callable[[], Awaitable[T]],
    lock_key: str,
    lock_ttl: int = 60,
    wait_timeout: float = 8.0,
    poll_interval: float = 0.3,
    fallback: Optional[Callable[[], Awaitable[Optional[T]]]] = None,
) -> T:
    """
    캐시 미스 상황에서 "동일 작업 중복 실행"을 막는 단일 비행(SingleFlight) 유틸.
    1) 캐시 확인
    2) 락 획득하면 create() 실행 후 cache_set()
    3) 락 못 얻으면 wait_timeout 동안 poll하며 캐시 재확인
    4) timeout 시 fallback() 시도 (있으면), 없으면 예외 발생
    """

    # 1) 캐시 먼저 확인
    cached = await cache_get()
    if cached is not None:
        return cached

    # 2) 락 획득 시도
    got_lock = await redis.set(lock_key, "1", ex=lock_ttl, nx=True)

    if got_lock:
        try:
            # (더블체크) 락 잡은 직후에도 캐시가 생겼을 수 있으므로 한번 더 확인
            cached2 = await cache_get()
            if cached2 is not None:
                return cached2

            # 생성자만 생성
            result = await create()
            await cache_set(result)
            return result
        finally:
            # 락 해제 (TTL이 있어도 빠르게 해제하는 게 좋음)
            try:
                await redis.delete(lock_key)
            except Exception:
                pass

    # 3) 락 실패: 누군가 생성 중 → 캐시가 생길 때까지 폴링
    waited = 0.0
    while waited < wait_timeout:
        await asyncio.sleep(poll_interval)
        waited += poll_interval

        cached3 = await cache_get()
        if cached3 is not None:
            return cached3

    # 4) 타임아웃 → fallback
    if fallback is not None:
        fb = await fallback()
        if fb is not None:
            # fallback 결과도 캐시에 넣어둘지 여부는 호출자가 결정하는 게 원칙이지만
            # 실무에선 넣는 게 대부분 유리함. 여기서는 호출자가 cache_set을 따로 호출하게 설계.
            return fb

    raise SingleFlightTimeout(f"singleflight timeout for lock_key={lock_key}")
