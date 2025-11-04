# /services/details_service.py

import asyncio 
import json
from fastapi import HTTPException
from fastapi.logger import logger
from sqlalchemy.orm import Session
import redis.asyncio as redis
from typing import Dict, List, Any

from repository import company_repository, summary_repository
from services import dart_api_service, news_service, groq_service
from schemas.company import CompanyInfo
from schemas.news import NewsArticle
from schemas.summary import RawFinancialEntry, SummaryCreate
from schemas.details import CompanyDetailResponse 
from utils.utils import _format_financial, _format_news_for_groq # 헬퍼 함수

INFO_TTL = 86400       # 24시간 (회사 개황)
FINANCIALS_TTL = 86400 # 24시간 (재무)
NEWS_TTL = 600         # 10분 (뉴스)
SUMMARY_TTL = 600      # 10분 (AI 요약 - Redis L1 전용)


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
        raise HTTPException(status_code=500, detail="회사 정보 조회 중 오류 발생")
    
    corp_code = str(company_info.corp_code) 

    # --- 2 & 3. 재무 및 뉴스 정보 (병렬 호출) ---
    financials_key = f"details:financials:{corp_code}"
    news_key = f"details:news:{name}"

    try:
        # 2. 재무 정보 (L1 -> L3)
        async def fetch_financials():
            cached_financials = await redis_client.get(financials_key)
            if cached_financials:
                return json.loads(cached_financials)
            
            raw_data = await dart_api_service.fetch_and_process_financials(corp_code)
            await redis_client.set(financials_key, json.dumps(raw_data), ex=FINANCIALS_TTL)
            return raw_data

        # 3. 뉴스 정보 (L1 -> L3)
        async def fetch_news():
            cached_news = await redis_client.get(news_key)
            if cached_news:
                return json.loads(cached_news)
            
            news_pydantic_models = await news_service.fetch_all_news_by_category(name)
            raw_data = {k: [a.dict() for a in v] for k, v in news_pydantic_models.items()}
            await redis_client.set(news_key, json.dumps(raw_data), ex=NEWS_TTL)
            return raw_data

        results = await asyncio.gather(fetch_financials(), fetch_news())
        raw_financial_data: Dict[str, Any] = results[0]
        raw_news_data: Dict[str, List[Dict]] = results[1]
        
    except Exception as e:
        raw_financial_data, raw_news_data = {}, {}


    # --- 4. AI 요약 (L1 -> L3 -> L2 Fallback) ---
    summary_key = f"details:summary:{name}"
    ai_summary_text: str = None
    
    try:
        cached_summary = await redis_client.get(summary_key)
        if cached_summary:
            ai_summary_text = cached_summary
    except Exception as e:
        logger.error(f"Redis GET 오류 (Summary): {e}")

    if not ai_summary_text:
        try:
            validated_financial_data = {k: RawFinancialEntry.parse_obj(v) for k, v in raw_financial_data.items() if isinstance(v, dict) and all(k in v for k in ["자본총계", "매출액"])}
            채용_news_list: List[NewsArticle] = []
            if isinstance(raw_news_data, dict):
                for category, articles in raw_news_data.items():
                    if category == "채용":
                        채용_news_list = [NewsArticle.parse_obj(a) for a in articles]
                        break

            has_fin = bool(validated_financial_data)
            has_news = bool(채용_news_list)
            
            if not has_fin and not has_news:
                ai_summary_text = "AI요약을 생성하기 위한 정보를 찾을 수 없습니다."
            else:
                fin_text = _format_financial(validated_financial_data) if has_fin else "재무정보 없음"
                news_text = _format_news_for_groq(채용_news_list) if has_news else "채용뉴스 없음"
                ai_summary_text = await groq_service.summarize(name, fin_text, news_text)
            
            # (AI Success) L2(RDB) & L1(Redis) 저장
            try:
                summary_data = SummaryCreate(company_name=name, summary_text=ai_summary_text)
                await asyncio.to_thread(summary_repository.update_summary, db, summary_data)
                await redis_client.set(summary_key, ai_summary_text, ex=SUMMARY_TTL)
            except Exception as e:
                logger.error(f"Cache SET 오류 (Origin->L1/L2): {e}")
                
        except Exception as e:
            rdb_summary = await asyncio.to_thread(summary_repository.get_recent_summary, db, name)
            if rdb_summary:
                ai_summary_text = rdb_summary.summary_text
            else:
                ai_summary_text = "AI 요약 생성에 실패했으며, 저장된 정보도 없습니다."

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