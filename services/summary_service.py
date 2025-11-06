# /services/summary_service.py

import asyncio
import redis.asyncio as redis
from sqlalchemy.orm import Session
from repository import summary_repository
from services import groq_service
from schemas.summary import SummaryCreate
from utils.utils import _format_financial, _format_news_for_groq
from core.database import SessionLocal

SUMMARY_TTL = 600 # 10분

class SummaryService:
    def __init__(self, redis_client: redis.Redis, SessionLocal):
        self.redis = redis_client
        self.SessionLocal = SessionLocal

    async def get_summary(self, name: str, financial_data, news_data):
        """(Worker) AI 요약의 L1 -> L3 -> L2(Fallback) 캐싱 로직 담당"""
        key = f"details:summary:{name}"
        
        # 1. (L1) Redis 조회
        cached = await self.redis.get(key)
        if cached:
            return cached
        
        db = self.SessionLocal()

        # 2. (L3) Groq AI 호출
        try:
            fin_text = _format_financial(financial_data)
            news_text = _format_news_for_groq(news_data.get("채용", []))
            ai_summary_text = await groq_service.summarize(name, fin_text, news_text)
            
            # (L1/L2 저장)
            summary_data = SummaryCreate(company_name=name, summary_text=ai_summary_text)
            await asyncio.to_thread(
                summary_repository.upsert_summary, db, summary_data
            )
            await asyncio.to_thread(db.commit) 
            
            await self.redis.set(key, ai_summary_text, ex=SUMMARY_TTL)
            return ai_summary_text
            
        except Exception as e:
            await asyncio.to_thread(db.rollback)
            # 3. (L2 Fallback) L3 실패 시 L2(RDB) 조회
            rdb_summary = await asyncio.to_thread(
                summary_repository.get_recent_summary, db, name
            )
            if rdb_summary:
                await self.redis.set(key, rdb_summary.summary_text, ex=SUMMARY_TTL)
                return rdb_summary.summary_text
            else:
                return "AI 요약 생성에 실패했으며, 저장된 정보도 없습니다."