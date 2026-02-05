# /services/summary_service.py

import asyncio
import redis.asyncio as redis
from sqlalchemy.orm import Session
from repository import summary_repository
from services import groq_service
from schemas.summary import SummaryCreate
from utils.utils import _format_financial, _format_news
from fastapi.logger import logger

SUMMARY_TTL = 600          # 요약 캐시 TTL (10분)
SUMMARY_LOCK_TTL = 60      # 락 TTL (60초)
LOCK_WAIT_TIMEOUT = 10     # 락 못 잡았을 때 최대 대기 시간(초)
LOCK_POLL_INTERVAL = 0.4   # 폴링 간격(초)

class SummaryService:
    def __init__(self, redis_client: redis.Redis, SessionLocal):
        self.redis = redis_client
        self.SessionLocal = SessionLocal

    async def get_summary(self, name: str, financial_data, news_data):
        summary_key = f"details:summary:{name}"
        lock_key = f"details:summary_lock:{name}"

        # 1) (L1) Redis 조회
        cached = await self.redis.get(summary_key)
        if cached:
            return cached

        # 2) 락 획득 시도 (SET NX EX)
        # - nx=True: 키가 없을 때만 set (락)
        # - ex=SUMMARY_LOCK_TTL: TTL로 데드락 방지
        got_lock = await self.redis.set(lock_key, "1", ex=SUMMARY_LOCK_TTL, nx=True)

        # 2-1) 락을 못 잡았으면: 누군가 요약 생성 중 → 잠깐 기다렸다가 캐시를 재조회
        if not got_lock:
            waited = 0.0
            while waited < LOCK_WAIT_TIMEOUT:
                await asyncio.sleep(LOCK_POLL_INTERVAL)
                waited += LOCK_POLL_INTERVAL

                cached = await self.redis.get(summary_key)
                if cached:
                    return cached

            # 여기까지 왔으면 "생성자"가 너무 오래 걸렸거나 실패했을 수 있음
            # → DB fallback 시도
            db = self.SessionLocal()
            try:
                rdb_summary = await asyncio.to_thread(
                    summary_repository.get_recent_summary, db, name
                )
                if rdb_summary:
                    await self.redis.set(summary_key, rdb_summary.summary_text, ex=SUMMARY_TTL)
                    return rdb_summary.summary_text
                return "AI 요약 생성 중 지연이 발생했습니다. 잠시 후 다시 시도해주세요."
            finally:
                await asyncio.to_thread(db.close)

        # 3) 락을 잡은 경우: 내가 '생성자'
        db = self.SessionLocal()
        try:
            # (중요) 락 잡고 나서도 혹시 누가 이미 만들어뒀을 수 있으니 더블체크
            cached = await self.redis.get(summary_key)
            if cached:
                return cached

            fin_text = _format_financial(financial_data)
            news_text = _format_news(news_data.get("채용", []))

            ai_summary_text = await groq_service.summarize(name, fin_text, news_text)

            # (L2 저장) DB upsert
            summary_data = SummaryCreate(company_name=name, summary_text=ai_summary_text)
            await asyncio.to_thread(summary_repository.upsert_summary, db, summary_data)
            await asyncio.to_thread(db.commit)

            # (L1 저장) Redis
            await self.redis.set(summary_key, ai_summary_text, ex=SUMMARY_TTL)
            return ai_summary_text

        except Exception as e:
            logger.error(f"[SUMMARY] 생성 실패: {e}")

            await asyncio.to_thread(db.rollback)

            # 4) (L2 Fallback) Groq 실패 시 DB 조회
            rdb_summary = await asyncio.to_thread(
                summary_repository.get_recent_summary, db, name
            )
            if rdb_summary:
                await self.redis.set(summary_key, rdb_summary.summary_text, ex=SUMMARY_TTL)
                return rdb_summary.summary_text

            return "AI 요약 생성에 실패했으며, 저장된 정보도 없습니다."

        finally:
            # 5) 락 해제 + DB close (락은 생성자만 해제)
            try:
                await self.redis.delete(lock_key)
            except Exception as e:
                logger.error(f"[SUMMARY] 락 해제 실패: {e}")

            await asyncio.to_thread(db.close)
