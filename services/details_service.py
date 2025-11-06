# /services/details_service.py (최종 수정)

import asyncio 
import json
from fastapi import HTTPException
from fastapi.logger import logger
from sqlalchemy.orm import Session
import redis.asyncio as redis
from typing import Dict, List, Any
from core.database import SessionLocal

from repository import company_repository 
from services.financial_service import FinancialService
from services.news_service import NewsService
from services.summary_service import SummaryService
from schemas.company import CompanyInfo
from schemas.details import CompanyDetailResponse 
from schemas.summary import RawFinancialEntry
from schemas.news import NewsArticle

INFO_TTL = 86400

async def get_company_details(
    name: str, 
    db: Session,
    redis_client: redis.Redis
) -> CompanyDetailResponse:
    
    # --- 1. 회사 개황 정보 (Info) ---
    info_key = f"details:info:{name}"
    company_info: CompanyInfo = None
    try:
        cached_info = await redis_client.get(info_key)
        if cached_info:
            company_info = CompanyInfo.parse_raw(cached_info)
        else:
            company_info_orm = await asyncio.to_thread(
                company_repository.get_company_by_name_exact, db, name
            )
            if not company_info_orm:
                raise HTTPException(status_code=404, detail="해당 회사명을 찾을 수 없습니다.")
            company_info = CompanyInfo.from_orm(company_info_orm)
            await redis_client.set(info_key, company_info.json(), ex=INFO_TTL)
    except Exception as e:
        await asyncio.to_thread(db.rollback)
        raise HTTPException(status_code=500, detail=f"회사 정보 조회 중 오류: {e}")
    
    corp_code = str(company_info.corp_code) 

    # --- 2 & 3. 재무 및 뉴스 정보 (병렬 호출) ---
    fin_service = FinancialService(redis_client, SessionLocal)
    news_service = NewsService(redis_client, SessionLocal)
    
    try:
        results = await asyncio.gather(
            fin_service.get_financials(corp_code),
            news_service.get_news(name, corp_code)
        )
        raw_financial_data: Dict[str, Any] = results[0]
        raw_news_data: Dict[str, List[Dict]] = results[1]
    except Exception as e:
        await asyncio.to_thread(db.rollback)
        raise HTTPException(status_code=500, detail=f"재무/뉴스 처리 오류: {e}")


    # --- 4. AI 요약 (순차 호출) ---
    summary_service = SummaryService(redis_client, SessionLocal)
    try:
        ai_summary_text = await summary_service.get_summary(
            name, raw_financial_data, raw_news_data
        )
    except Exception as e:
        await asyncio.to_thread(db.rollback)
        raise HTTPException(status_code=500, detail=f"AI 요약 처리 오류: {e}")

    # --- 5. 최종 조합 및 반환 ---
    try:
        final_validated_financials = {k: RawFinancialEntry.parse_obj(v) for k, v in raw_financial_data.items() if isinstance(v, dict) and all(k in v for k in ["자본총계", "매출액"])}
        final_validated_news = {k: [NewsArticle.parse_obj(a) for a in v] for k, v in raw_news_data.items()}
    except Exception as e:
        raise HTTPException(status_code=500, detail="데이터 조합 중 오류 발생")

    return CompanyDetailResponse(
        company_info=company_info,
        financial_data=final_validated_financials,
        news_data=final_validated_news,
        ai_summary=ai_summary_text
    )