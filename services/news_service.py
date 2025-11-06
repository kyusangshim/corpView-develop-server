import json
import asyncio
import redis.asyncio as redis
from repository import news_repository
from clients import naver_news_client
from utils.utils import _format_news_from_orm
from core.database import SessionLocal
from sqlalchemy.orm import Session
from fastapi.logger import logger

CATEGORIES = ["전체", "채용", "주가", "노사", "IT"]
NEWS_TTL = 600

class NewsService:
    def __init__(self, redis_client: redis.Redis, SessionLocal):
        self.redis = redis_client
        self.SessionLocal = SessionLocal

    async def _save_to_l2_background(self, corp_code: str, data: dict):
        """(Helper) L2 저장을 별도 스레드와 세션에서 'Fire and Forget'으로 실행"""
        db: Session = SessionLocal() # 3. 이 작업을 위한 새 세션 생성
        try:
            await asyncio.to_thread(news_repository.upsert_news_articles, db, corp_code, data)
            await asyncio.to_thread(db.commit) # 4. 작업 단위 커밋
        except Exception as e:
            await asyncio.to_thread(db.rollback)
        finally:
            await asyncio.to_thread(db.close) # 5. 세션 닫기
    

    async def get_news(self, name: str, corp_code: str):
        key = f"details:news:{name}"

        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        db: Session = SessionLocal()

        try:
            # 1. Naver API 호출 (병렬)
            async def fetch_category(cat: str):
                query = name if cat == "전체" else f"{name} {cat}"
                return await naver_news_client.fetch_news_by_query(query)

            tasks = [fetch_category(cat) for cat in CATEGORIES]
            results = await asyncio.gather(*tasks)
            raw_data = {cat: [a.dict() for a in lst] for cat, lst in zip(CATEGORIES, results)}

            # [수정] L1 저장은 "즉시" 실행
            await self.redis.set(key, json.dumps(raw_data), ex=NEWS_TTL)
            
            # [수정] L2 저장은 "백그라운드"로 실행
            asyncio.create_task(self._save_to_l2_background(corp_code, raw_data))

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
