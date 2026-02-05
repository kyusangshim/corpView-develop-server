# services/summary_service.py

import asyncio
import redis.asyncio as redis
from sqlalchemy.orm import Session

from domains.summary import repository as summary_repository
from clients import groq_client
from domains.summary.schema import SummaryCreate
from utils.utils import _format_financial, _format_news

from core.cache_keys import details_summary_key, lock_key
from core.cached_singleflight import cached_singleflight_str

SUMMARY_TTL = 600

SUMMARY_LOCK_TTL = 60
SUMMARY_WAIT_TIMEOUT = 10
SUMMARY_POLL = 0.4


class SummaryService:
    def __init__(self, redis_client: redis.Redis, SessionLocal):
        self.redis = redis_client
        self.SessionLocal = SessionLocal

    async def get_summary(self, name: str, financial_data, news_data):
        cache_key = details_summary_key(name)
        lk = lock_key("summary", name)

        async def create() -> str:
            db: Session = self.SessionLocal()
            try:
                fin_text = _format_financial(financial_data)
                news_text = _format_news(news_data.get("채용", []))
                ai_summary_text = await groq_client.summarize(name, fin_text, news_text)

                summary_data = SummaryCreate(company_name=name, summary_text=ai_summary_text)
                await asyncio.to_thread(summary_repository.upsert_summary, db, summary_data)
                await asyncio.to_thread(db.commit)

                return ai_summary_text
            except Exception:
                await asyncio.to_thread(db.rollback)
                raise
            finally:
                await asyncio.to_thread(db.close)

        async def fallback():
            db: Session = self.SessionLocal()
            try:
                rdb_summary = await asyncio.to_thread(
                    summary_repository.get_recent_summary, db, name
                )
                if rdb_summary:
                    return rdb_summary.summary_text
                return None
            finally:
                await asyncio.to_thread(db.close)

        return await cached_singleflight_str(
            redis=self.redis,
            cache_key=cache_key,
            ttl=SUMMARY_TTL,
            lock_key=lk,
            lock_ttl=SUMMARY_LOCK_TTL,
            wait_timeout=SUMMARY_WAIT_TIMEOUT,
            poll_interval=SUMMARY_POLL,
            create=create,
            fallback=fallback,
        )
