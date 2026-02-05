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
NEWS_LOCK_TTL = 30          # 뉴스 생성 락 TTL
LOCK_WAIT_TIMEOUT = 8       # 최대 대기
LOCK_POLL_INTERVAL = 0.3

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
        lock_key = f"details:news_lock:{name}"

        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        # 락 시도
        got_lock = await self.redis.set(lock_key, "1", ex=NEWS_LOCK_TTL, nx=True)

        # 락 실패: 누군가 생성 중 → 잠깐 기다렸다 캐시 재조회
        if not got_lock:
            waited = 0.0
            while waited < LOCK_WAIT_TIMEOUT:
                await asyncio.sleep(LOCK_POLL_INTERVAL)
                waited += LOCK_POLL_INTERVAL

                cached = await self.redis.get(key)
                if cached:
                    return json.loads(cached)

            # 너무 오래 걸리면 L2 fallback
            db: Session = SessionLocal()
            try:
                l2_data = await asyncio.to_thread(news_repository.get_cached_news_by_code, db, corp_code)
                if l2_data:
                    raw_data = _format_news_from_orm(l2_data)
                    await self.redis.set(key, json.dumps(raw_data), ex=NEWS_TTL)
                    return raw_data
                return {}
            finally:
                await asyncio.to_thread(db.close)

        # 락 성공: 내가 생성자
        db: Session = SessionLocal()
        try:
            # 더블체크
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)

            async def fetch_category(cat: str):
                query = name if cat == "전체" else f"{name} {cat}"
                return await naver_news_client.fetch_news_by_query(query)

            tasks = [fetch_category(cat) for cat in CATEGORIES]
            results = await asyncio.gather(*tasks)
            raw_data = {cat: [a.dict() for a in lst] for cat, lst in zip(CATEGORIES, results)}

            await self.redis.set(key, json.dumps(raw_data), ex=NEWS_TTL)
            asyncio.create_task(self._save_to_l2_background(corp_code, raw_data))
            return raw_data

        except Exception as e:
            await asyncio.to_thread(db.rollback)
            # fallback
            l2_data = await asyncio.to_thread(news_repository.get_cached_news_by_code, db, corp_code)
            if l2_data:
                raw_data = _format_news_from_orm(l2_data)
                await self.redis.set(key, json.dumps(raw_data), ex=NEWS_TTL)
                return raw_data
            return {}

        finally:
            # 락 해제
            try:
                await self.redis.delete(lock_key)
            except Exception:
                pass
            await asyncio.to_thread(db.close)
