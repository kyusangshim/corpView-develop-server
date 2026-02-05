# services/details_usecase.py

import asyncio
from fastapi import HTTPException
from sqlalchemy.orm import Session
import redis.asyncio as redis
from typing import Dict, List, Any

from repository import company_repository
from services.financial_service import FinancialService
from services.news_service import NewsService
from services.summary_service import SummaryService

from schemas.company import CompanyInfo
from schemas.details import CompanyDetailResponse
from schemas.summary import RawFinancialEntry
from schemas.news import NewsArticle

from core.cache_keys import details_info_key

INFO_TTL = 86400  # 24시간


class DetailsUseCase:
    """
    회사 상세 응답을 "조합"하는 유스케이스(오케스트레이터).
    - 회사 개황(info)
    - 재무(financials)
    - 뉴스(news)
    - AI 요약(summary)
    을 모아 CompanyDetailResponse로 반환한다.
    """

    def __init__(
        self,
        db: Session,
        redis_client: redis.Redis,
        financial_service: FinancialService,
        news_service: NewsService,
        summary_service: SummaryService,
    ):
        self.db = db
        self.redis = redis_client
        self.financial_service = financial_service
        self.news_service = news_service
        self.summary_service = summary_service

    async def get_company_details(self, name: str) -> CompanyDetailResponse:
        # 1) 회사 개황
        company_info = await self._get_company_info(name)
        corp_code = str(company_info.corp_code)

        # 2) 재무/뉴스 병렬
        try:
            raw_financial_data, raw_news_data = await asyncio.gather(
                self.financial_service.get_financials(corp_code),
                self.news_service.get_news(name, corp_code),
            )
        except Exception as e:
            # 여기서 rollback을 강제하지 않는 이유:
            # - 이 유스케이스는 대부분 read 흐름이고
            # - write는 각 서비스가 별도 세션에서 처리(Fire-and-Forget)하고 있기 때문
            raise HTTPException(status_code=500, detail=f"재무/뉴스 처리 오류: {e}")

        # 3) AI 요약(순차)
        try:
            ai_summary_text = await self.summary_service.get_summary(
                name, raw_financial_data, raw_news_data
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI 요약 처리 오류: {e}")

        # 4) 응답 스키마 변환/검증 (조합부를 함수로 분리하면 더 깔끔해짐)
        try:
            final_validated_financials = {
                k: RawFinancialEntry.parse_obj(v)
                for k, v in raw_financial_data.items()
                if isinstance(v, dict) and all(x in v for x in ["자본총계", "매출액"])
            }

            final_validated_news = {
                k: [NewsArticle.parse_obj(a) for a in v]
                for k, v in raw_news_data.items()
            }
        except Exception:
            raise HTTPException(status_code=500, detail="데이터 조합 중 오류 발생")

        return CompanyDetailResponse(
            company_info=company_info,
            financial_data=final_validated_financials,
            news_data=final_validated_news,
            ai_summary=ai_summary_text,
        )

    async def _get_company_info(self, name: str) -> CompanyInfo:
        key = details_info_key(name)

        cached = await self.redis.get(key)
        if cached:
            return CompanyInfo.parse_raw(cached)

        company_info_orm = await asyncio.to_thread(
            company_repository.get_company_by_name_exact, self.db, name
        )
        if not company_info_orm:
            raise HTTPException(status_code=404, detail="해당 회사명을 찾을 수 없습니다.")

        company_info = CompanyInfo.from_orm(company_info_orm)
        await self.redis.set(key, company_info.json(), ex=INFO_TTL)
        return company_info
