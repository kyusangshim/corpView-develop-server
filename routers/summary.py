# /routers/summary.py (리팩토링 후)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db

# 1. 스키마와 '서비스'만 임포트
from schemas.summary import SummaryOut, SummaryRequest
from services import summary_service # 3단계에서 새로 만든 서비스

# (prefix를 추가하여 /summary로 그룹화하는 것을 추천)
router = APIRouter()

@router.post("/", response_model=SummaryOut)
async def summarize_with_client_data(
    req: SummaryRequest, db: Session = Depends(get_db)
):
    
    return await summary_service.generate_and_save_summary(req, db)