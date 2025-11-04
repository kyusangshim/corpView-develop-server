# /routers/details_redis.py

import asyncio 
from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.logger import logger
from sqlalchemy.orm import Session
import redis.asyncio as redis # Redis 클라이언트 임포트
from core.database import get_db
from core.cache import get_redis # 2단계에서 만든 Redis 의존성 임포트
from typing import Dict, List, Any

# --- 의존성 임포트 (기존과 동일) ---
from repository import company_repository
from services import dart_api_service, news_service, groq_service
from schemas.company import CompanyInfo
from schemas.news import NewsArticle, AllNewsResponse
from schemas.summary import RawFinancialEntry
from schemas.details import CompanyDetailResponse 
from utils.utils import _format_financial, _format_news_for_groq

router = APIRouter()


@router.get("/company-details", response_model=CompanyDetailResponse)
async def get_integrated_company_details_cached(
    name: str = Query(...), 
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis) # Redis 의존성 주입
):
    """
    (BFF) 기업 상세 페이지 데이터를 통합 반환합니다.
    (Cache-Aside 패턴 적용 버전)
    """
    
    # 1. [CACHE GET] 캐시 키 생성
    cache_key = f"company-details:{name}"
    
    try:
        cached_data = await redis_client.get(cache_key)
        
        if cached_data:
            logger.info(f"Cache HIT for key: {cache_key}")
            # Pydantic v1의 parse_raw (JSON 문자열을 Pydantic 모델로)
            return CompanyDetailResponse.parse_raw(cached_data) 
            
    except Exception as e:
        # Redis가 죽어도 서비스는 계속되어야 합니다.
        logger.error(f"Redis GET 오류: {e} - 캐시 없이 진행")

    # 2. [CACHE MISS] 캐시가 없으면, 기존 로직 실행
    logger.info(f"Cache MISS for key: {cache_key}")
    
    # 2-1. (DB) 기업 개황 정보
    company_info_orm = company_repository.get_company_by_name_exact(db, name)
    if not company_info_orm:
        raise HTTPException(status_code=404, detail="해당 회사명을 찾을 수 없습니다.")
    company_info = CompanyInfo.from_orm(company_info_orm)
    corp_code = company_info.corp_code

    # 2-2. (API) 재무 & 뉴스 병렬 호출
    try:
        results = await asyncio.gather(
            dart_api_service.fetch_and_process_financials(str(corp_code)),
            news_service.fetch_all_news_by_category(name)
        )
        raw_financial_data: Dict[str, Any] = results[0]
        raw_news_data: Dict[str, List[Dict]] = results[1]
    except Exception as e:
        logger.error(f"DART/Naver API 병렬 호출 오류: {e}")
        raise HTTPException(status_code=500, detail=f"외부 API 호출 오류: {str(e)}")

    # 2-3. (API) AI 요약 생성
    try:
        # Pydantic 검증
        validated_financial_data: Dict[str, RawFinancialEntry] = {}
        if isinstance(raw_financial_data, dict) and "message" not in raw_financial_data:
            for year, entry in raw_financial_data.items():
                try:
                    validated_financial_data[year] = RawFinancialEntry.parse_obj(entry)
                except Exception: continue
        
        validated_news_data: AllNewsResponse = {}
        채용_news_list: List[NewsArticle] = []
        if isinstance(raw_news_data, dict):
            for category, articles in raw_news_data.items():
                try:
                    validated_articles = [NewsArticle.parse_obj(a) for a in articles]
                    validated_news_data[category] = validated_articles
                    if category == "채용":
                        채용_news_list = validated_articles
                except Exception: continue

        # Groq 입력 텍스트 준비
        has_fin = bool(validated_financial_data)
        has_news = bool(채용_news_list)
        
        if not has_fin and not has_news:
            ai_summary_text = "AI요약을 생성하기 위한 정보를 찾을 수 없습니다."
        else:
            fin_text = _format_financial(validated_financial_data) 
            news_text = _format_news_for_groq(채용_news_list)
            ai_summary_text = await groq_service.summarize(name, fin_text, news_text)
    except Exception as e:
        logger.error(f"AI 요약 생성 오류: {e}")
        ai_summary_text = "AI 요약 생성 중 오류가 발생했습니다."

    # 3. [CACHE SET] 최종 응답 객체 생성
    final_response = CompanyDetailResponse(
        company_info=company_info,
        financial_data=validated_financial_data,
        news_data=validated_news_data,
        ai_summary=ai_summary_text
    )
    
    # 4. 객체를 JSON 문자열로 변환하여 Redis에 저장 (1시간 TTL)
    try:
        # Pydantic v1의 .json()
        await redis_client.set(cache_key, final_response.json(), ex=3600) 
        logger.info(f"Cache SET for key: {cache_key}")
    except Exception as e:
        # 캐시 저장이 실패해도 사용자에게는 응답을 보내야 합니다.
        logger.error(f"Redis SET 오류: {e}")

    # 5. 최종 응답 반환
    return final_response