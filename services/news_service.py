import json
import asyncio
import redis.asyncio as redis
from repository import news_repository
from clients import naver_news_client
from utils.utils import _format_news_from_orm

CATEGORIES = ["전체", "채용", "주가", "노사", "IT"]
NEWS_TTL = 600

class NewsService:
    def __init__(self, redis_client: redis.Redis, SessionLocal):
        self.redis = redis_client
        self.SessionLocal = SessionLocal

    async def get_news(self, name: str, corp_code: str):
        key = f"details:news:{name}"

        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        db = self.SessionLocal()

        try:
            # 1. Naver API 호출 (병렬)
            async def fetch_category(cat: str):
                query = name if cat == "전체" else f"{name} {cat}"
                return await naver_news_client.fetch_news_by_query(query)

            tasks = [fetch_category(cat) for cat in CATEGORIES]
            results = await asyncio.gather(*tasks)
            raw_data = {cat: [a.dict() for a in lst] for cat, lst in zip(CATEGORIES, results)}

            # L2 저장
            await asyncio.to_thread(news_repository.upsert_news_articles, db, corp_code, raw_data)
            await asyncio.to_thread(db.commit)
            await self.redis.set(key, json.dumps(raw_data), ex=NEWS_TTL)
            return raw_data

        except Exception:
            await asyncio.to_thread(db.rollback)
            # Fallback to L2
            l2_data = await asyncio.to_thread(news_repository.get_cached_news_by_code, db, corp_code)
            if l2_data:
                raw_data = _format_news_from_orm(l2_data)
                await self.redis.set(key, json.dumps(raw_data), ex=NEWS_TTL)
                return raw_data
            return {}
        finally:
            await asyncio.to_thread(db.close)
