# core/db_background.py

import asyncio
from typing import Any, Callable


def fire_and_forget_db(
    SessionLocal,
    work_fn: Callable[..., Any],
    *args,
    **kwargs,
) -> None:
    """
    DB 저장 같은 작업을 "별도 세션"에서 Fire-and-Forget으로 수행.
    - work_fn: 동기 함수(대부분 repository 함수)
    - *args/**kwargs: work_fn에 전달될 인자들
    """

    async def _run():
        db = SessionLocal()
        try:
            await asyncio.to_thread(work_fn, db, *args, **kwargs)
            await asyncio.to_thread(db.commit)
        except Exception:
            await asyncio.to_thread(db.rollback)
        finally:
            await asyncio.to_thread(db.close)

    asyncio.create_task(_run())
