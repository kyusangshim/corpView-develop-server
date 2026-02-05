# core/deps.py

from fastapi import Depends
from sqlalchemy.orm import Session
import redis.asyncio as redis

from core.database import get_db, SessionLocal
from core.cache import get_redis

from services.financial_service import FinancialService
from services.news_service import NewsService
from services.summary_service import SummaryService
from domains.details.usecase import DetailsUseCase


def get_financial_service(
    redis_client: redis.Redis = Depends(get_redis),
) -> FinancialService:
    return FinancialService(redis_client, SessionLocal)


def get_news_service(
    redis_client: redis.Redis = Depends(get_redis),
) -> NewsService:
    return NewsService(redis_client, SessionLocal)


def get_summary_service(
    redis_client: redis.Redis = Depends(get_redis),
) -> SummaryService:
    return SummaryService(redis_client, SessionLocal)


def get_details_usecase(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    financial_service: FinancialService = Depends(get_financial_service),
    news_service: NewsService = Depends(get_news_service),
    summary_service: SummaryService = Depends(get_summary_service),
) -> DetailsUseCase:
    return DetailsUseCase(
        db=db,
        redis_client=redis_client,
        financial_service=financial_service,
        news_service=news_service,
        summary_service=summary_service,
    )
