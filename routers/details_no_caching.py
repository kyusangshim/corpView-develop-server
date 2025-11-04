# /routers/details.py

import asyncio 
from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.logger import logger
from sqlalchemy.orm import Session
from core.database import get_db
from typing import Dict, List, Any

from repository import company_repository
from services import dart_api_service, news_service, groq_service

from schemas.company import CompanyInfo
from schemas.news import NewsArticle, AllNewsResponse
from schemas.summary import RawFinancialEntry
from schemas.details import CompanyDetailResponse 

from utils.utils import _format_financial, _format_news, _format_news_for_groq

router = APIRouter()

@router.get("/company-details", response_model=CompanyDetailResponse)
async def get_integrated_company_details(
    name: str = Query(...), db: Session = Depends(get_db)
):
    """
    (BFF) 기업 상세 페이지에 필요한 모든 데이터를 통합하여 반환합니다.
    (캐시 미적용 버전)
    """
    
    # 1. (DB) 기업 개황 정보 조회 (프론트 1번 작업)
    company_info_orm = company_repository.get_company_by_name_exact(db, name)
    if not company_info_orm:
        raise HTTPException(status_code=404, detail="해당 회사명을 찾을 수 없습니다.")
    
    # ORM 객체를 Pydantic 스키마로 변환
    company_info = CompanyInfo.from_orm(company_info_orm)

    try:
        results = await asyncio.gather(
            dart_api_service.fetch_and_process_financials(str(company_info.corp_code)),
            news_service.fetch_all_news_by_category(name)
        )
        raw_financial_data: Dict[str, Any] = results[0]
        raw_news_data: Dict[str, List[Dict]] = results[1]

    except Exception as e:
        logger.error(f"DART/Naver API 병렬 호출 오류: {e}")
        raise HTTPException(status_code=500, detail=f"외부 API 호출 오류: {str(e)}")

    # 4. (API) AI 요약 생성 (프론트 4번 작업)
    try:
        # 4a. Pydantic으로 원시 데이터(dict)를 스키마(model)로 검증
        validated_financial_data: Dict[str, RawFinancialEntry] = {}
        if isinstance(raw_financial_data, dict) and "message" not in raw_financial_data:
            for year, entry in raw_financial_data.items():
                try:
                    # Pydantic v1 스타일 검증
                    validated_financial_data[year] = RawFinancialEntry.parse_obj(entry)
                except Exception:
                    continue # 검증 실패 시 해당 연도 스킵
        
        validated_news_data: AllNewsResponse = {}
        채용_news_list: List[NewsArticle] = []
        if isinstance(raw_news_data, dict):
            for category, articles in raw_news_data.items():
                try:
                    validated_articles = [NewsArticle.parse_obj(a) for a in articles]
                    validated_news_data[category] = validated_articles
                    if category == "채용":
                        채용_news_list = validated_articles
                except Exception:
                    continue # 검증 실패 시 해당 카테고리 스킵

        # 4b. Groq 입력 텍스트 준비
        has_fin = bool(validated_financial_data)
        has_news = bool(채용_news_list)
        
        if not has_fin and not has_news:
            ai_summary_text = "AI요약을 생성하기 위한 정보를 찾을 수 없습니다."
        else:
            fin_text = (
                _format_financial(validated_financial_data) 
                if has_fin 
                else "재무정보가 제공되지 않았습니다."
            )
            news_text = (
                _format_news_for_groq(채용_news_list) 
                if has_news 
                else "채용 관련 뉴스정보가 제공되지 않았습니다."
            )
            print(news_text)
            
            # 4c. Groq 서비스 호출
            ai_summary_text = await groq_service.summarize(name, fin_text, news_text)

    except Exception as e:
        logger.error(f"AI 요약 생성 오류: {e}")
        ai_summary_text = "AI 요약 생성 중 오류가 발생했습니다."

    # 5. 모든 데이터 조합하여 최종 응답 반환
    return CompanyDetailResponse(
        company_info=company_info,
        financial_data=validated_financial_data,
        news_data=validated_news_data,
        ai_summary=ai_summary_text
    )