# /routers/details_final.py

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
import redis.asyncio as redis
from core.database import get_db
from core.cache import get_redis

from schemas.details import CompanyDetailResponse 
from services import details_service # 1단계에서 만든 서비스

router = APIRouter()

@router.get("/company-details", response_model=CompanyDetailResponse)
async def get_integrated_company_details_final(
    name: str = Query(...), 
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    
    return await details_service.get_company_details(name, db, redis_client)