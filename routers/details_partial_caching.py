# /routers/details_final.py

import asyncio 
import json
from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.logger import logger
from sqlalchemy.orm import Session
import redis.asyncio as redis
from core.database import get_db
from core.cache import get_redis
from typing import Dict, List, Any

# --- 의존성 임포트 ---
from repository import company_repository, summary_repository # (summary_repository 임포트)
from services import dart_api_service, news_service, groq_service
from schemas.company import CompanyInfo
from schemas.news import NewsArticle, AllNewsResponse
from schemas.summary import RawFinancialEntry, SummaryCreate # (SummaryCreate 임포트)
from schemas.details import CompanyDetailResponse 
from utils.utils import _format_financial, _format_news_for_groq


router = APIRouter() # (최종 API)

# --- TTL 상수 정의 (AI 요약의 RDB TTL 제거) ---
INFO_TTL = 86400       # 24시간 (회사 개황)
FINANCIALS_TTL = 43200 # 12시간 (재무)
NEWS_TTL = 600         # 10분 (뉴스)
SUMMARY_TTL = 600      # 10분 (AI 요약 - Redis L1 전용)


@router.get("/company-details", response_model=CompanyDetailResponse)
async def get_integrated_company_details_final(
    name: str = Query(...), 
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    (BFF) 부분 캐싱 + L2(RDB) Fallback 전략 적용
    """

    info_key = f"details:info:{name}"
    company_info: CompanyInfo = None
    try:
        cached_info = await redis_client.get(info_key)
        if cached_info:
            company_info = CompanyInfo.parse_raw(cached_info)
        else:
            company_info_orm = company_repository.get_company_by_name_exact(db, name)
            if not company_info_orm:
                raise HTTPException(status_code=404, detail="해당 회사명을 찾을 수 없습니다.")
            company_info = CompanyInfo.from_orm(company_info_orm)
            await redis_client.set(info_key, company_info.json(), ex=INFO_TTL)
    except Exception as e:
        raise HTTPException(status_code=500, detail="회사 정보 조회 중 오류 발생")
    corp_code = company_info.corp_code

    # (2. 재무 정보 로직 ...)
    financials_key = f"details:financials:{corp_code}"
    raw_financial_data: Dict[str, Any] = None 
    try:
        cached_financials = await redis_client.get(financials_key)
        if cached_financials:
            raw_financial_data = json.loads(cached_financials)
        else:
            raw_financial_data = await dart_api_service.fetch_and_process_financials(str(corp_code))
            await redis_client.set(financials_key, json.dumps(raw_financial_data), ex=FINANCIALS_TTL)
    except Exception as e:
        raw_financial_data = {}

    # (3. 뉴스 정보 로직 ...)
    news_key = f"details:news:{name}"
    raw_news_data: Dict[str, List[Dict]] = None 
    try:
        cached_news = await redis_client.get(news_key)
        if cached_news:
            raw_news_data = json.loads(cached_news)
        else:
            news_pydantic_models = await news_service.fetch_all_news_by_category(name)
            raw_news_data = {k: [a.dict() for a in v] for k, v in news_pydantic_models.items()}
            await redis_client.set(news_key, json.dumps(raw_news_data), ex=NEWS_TTL)
    except Exception as e:
        raw_news_data = {}
        
    # --- 4. AI 요약 (Summary - L1(Redis) -> L3(AI) -> L2(RDB) Fallback) ---
    summary_key = f"details:summary:{name}"
    ai_summary_text: str = None
    
    # (Try L1) Redis 캐시 확인 (10분 TTL)
    try:
        cached_summary = await redis_client.get(summary_key)
        if cached_summary:
            logger.info(f"Cache HIT (L1 - Redis) for summary: {summary_key}")
            ai_summary_text = cached_summary
    except Exception as e:
        logger.error(f"Redis GET 오류 (Summary): {e}")

    # (Try L3) L1 캐시가 없으면, AI(Origin) 호출
    if not ai_summary_text:
        logger.info(f"Cache MISS (L1 - Redis) for summary: {summary_key}. Calling Groq AI.")
        
        try:
            # (데이터 검증 및 포맷팅)
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
                
                # [L3] Groq AI 호출
                ai_summary_text = await groq_service.summarize(name, fin_text, news_text)
            
            # [AI Success] L3 -> L2(RDB) & L1(Redis) 저장
            try:
                # L2(RDB) 영구 저장 (Upsert)
                summary_data = SummaryCreate(company_name=name, summary_text=ai_summary_text)
                summary_repository.update_summary(db, summary_data) 
                
                # L1(Redis) 핫 캐시 저장
                await redis_client.set(summary_key, ai_summary_text, ex=SUMMARY_TTL)
                logger.info(f"Cache SET (L1 & L2) for summary: {summary_key}")
                
            except Exception as e:
                logger.error(f"Cache SET 오류 (Origin->L1/L2): {e}")
                
        except Exception as e:
            # [AI Fail] L3(AI) 호출 실패! -> L2(RDB) Fallback 시도
            logger.error(f"AI(L3) 호출 실패: {e}. L2(RDB) Fallback 시도.")
            
            rdb_summary = summary_repository.get_recent_summary(db, name)
            if rdb_summary:
                logger.info(f"Cache HIT (L2 - RDB Fallback) for summary: {name}")
                ai_summary_text = rdb_summary.summary_text
            else:
                logger.info(f"Cache MISS (L2 - RDB Fallback) for summary: {name}")
                ai_summary_text = "AI 요약 생성에 실패했으며, 저장된 정보도 없습니다."

    # --- 5. 최종 조합 및 반환 ---
    try:
        final_validated_financials = {k: RawFinancialEntry.parse_obj(v) for k, v in raw_financial_data.items() if isinstance(v, dict) and all(k in v for k in ["자본총계", "매출액"])}
        final_validated_news = {k: [NewsArticle.parse_obj(a) for a in v] for k, v in raw_news_data.items()}
    except Exception as e:
        logger.error(f"최종 Pydantic 파싱 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터 조합 중 오류 발생")

    return CompanyDetailResponse(
        company_info=company_info,
        financial_data=final_validated_financials,
        news_data=final_validated_news,
        ai_summary=ai_summary_text
    )