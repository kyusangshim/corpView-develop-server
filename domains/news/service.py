# domains/news/service.py

import asyncio
from sqlalchemy.orm import Session
import redis.asyncio as redis

from clients import naver_news_client
from utils.utils import _format_news_from_orm
from core.database import SessionLocal

from core.cache_keys import details_news_key, lock_key
from core.cached_singleflight import cached_singleflight_json
from core.db_background import fire_and_forget_db

from domains.news import repository as news_repository

CATEGORIES = ["전체", "채용", "주가", "노사", "IT"]
NEWS_TTL = 600

NEWS_LOCK_TTL = 30
NEWS_WAIT_TIMEOUT = 8
NEWS_POLL = 0.3


class NewsService:
    def __init__(self, redis_client: redis.Redis, SessionLocal):
        self.redis = redis_client
        self.SessionLocal = SessionLocal

    async def get_news(self, name: str, corp_code: str):
        cache_key = details_news_key(name)
        lk = lock_key("news", name)

        async def create() -> dict:
            async def fetch_category(cat: str):
                query = name if cat == "전체" else f"{name} {cat}"
                return await naver_news_client.fetch_news_by_query(query)

            results = await asyncio.gather(*[fetch_category(c) for c in CATEGORIES])
            raw_data = {cat: [a.dict() for a in lst] for cat, lst in zip(CATEGORIES, results)}

            # L2 저장은 Fire-and-Forget
            fire_and_forget_db(
                self.SessionLocal,
                news_repository.upsert_news_articles,
                corp_code,
                raw_data,
            )
            return raw_data

        async def fallback():
            db: Session = self.SessionLocal()
            try:
                l2_data = await asyncio.to_thread(
                    news_repository.get_cached_news_by_code, db, corp_code
                )
                if l2_data:
                    return _format_news_from_orm(l2_data)
                return None
            finally:
                await asyncio.to_thread(db.close)

        return await cached_singleflight_json(
            redis=self.redis,
            cache_key=cache_key,
            ttl=NEWS_TTL,
            lock_key=lk,
            lock_ttl=NEWS_LOCK_TTL,
            wait_timeout=NEWS_WAIT_TIMEOUT,
            poll_interval=NEWS_POLL,
            create=create,
            fallback=fallback,
        )
