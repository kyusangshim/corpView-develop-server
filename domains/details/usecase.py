import asyncio
from fastapi import HTTPException
from sqlalchemy.orm import Session
import redis.asyncio as redis

from domains.companies import repository as company_repository
from domains.financials.service import FinancialService
from domains.news.service import NewsService
from domains.summary.service import SummaryService

from domains.companies.schema import CompanyInfo
from domains.details.schema import CompanyDetailResponse
from domains.summary.schema import RawFinancialEntry
from domains.news.schema import NewsArticle

from core.Redis.keys import details_info_key

INFO_TTL = 86400


class DetailsUseCase:
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
        company_info = await self._get_company_info(name)
        corp_code = str(company_info.corp_code)

        try:
            raw_financial_data, raw_news_data = await asyncio.gather(
                self.financial_service.get_financials(corp_code),
                self.news_service.get_news(name, corp_code),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"재무/뉴스 처리 오류: {e}")

        try:
            ai_summary_text = await self.summary_service.get_summary(
                name, raw_financial_data, raw_news_data
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI 요약 처리 오류: {e}")

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
