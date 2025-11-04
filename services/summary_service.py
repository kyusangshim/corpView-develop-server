# /services/summary_service.py (신규 생성)

from fastapi import HTTPException
from fastapi.logger import logger
from sqlalchemy.orm import Session
from utils.utils import _format_financial, _format_news

# 1. 의존성 임포트 (Repository, Service, Schema)
from repository import summary_repository
from services import groq_service
from schemas.summary import (
    SummaryCreate,
    SummaryOut,
    SummaryRequest,
)

# 3. 메인 비즈니스 로직 (라우터에서 이동)
async def generate_and_save_summary(
    req: SummaryRequest, db: Session
) -> SummaryOut:
    """
    AI 요약을 생성하고, DB에 Upsert(생성 또는 갱신)하는
    비즈니스 로직을 처리합니다.
    """
    
    # 1) 이미 저장된 요약이 있는지 확인 (Repository 호출)
    existing = summary_repository.get_recent_summary(db, req.company_name)

    # 2) 텍스트 포맷 변환
    has_fin = req.financial
    has_news = req.news.get("채용")

    if not has_fin and not has_news:
        summary_text = "AI요약을 생성하기 위한 정보를 찾을 수 없습니다."
    else:
        fin_text = (
            _format_financial(req.financial)
            if has_fin
            else "재무정보가 제공되지 않았습니다."
        )
        news_text = (
            _format_news(req.news.get("채용", []))
            if has_news
            else "채용 관련 뉴스정보가 제공되지 않았습니다."
        )

        # 3) Groq 요약 호출 (Service 호출)
        try:
            summary_text = await groq_service.summarize(
                req.company_name, fin_text, news_text
            )
        except HTTPException as e: # groq_service가 발생시킨 예외를 잡음
            logger.error(f"Groq API 호출 오류: {e.detail}")
            if e.status_code == 503:
                summary_text = "요약 서비스를 이용할 수 없습니다. 잠시 후 다시 시도해주세요."
            else:
                raise HTTPException(
                    status_code=500, detail="요약 처리 중 오류가 발생했습니다."
                )
        except Exception as e:
            # 기타 예기치 않은 오류
            logger.error(f"요약 처리 중 알 수 없는 오류: {e}")
            raise HTTPException(status_code=500, detail="서버 내부 오류")

    # 4) SummaryCreate 스키마로 데이터 준비
    summary_data = SummaryCreate(
        company_name=req.company_name, summary_text=summary_text
    )

    # 5) Upsert 로직 (Repository 호출)
    if existing:
        summary_data = SummaryCreate(company_name=req.company_name, summary_text=summary_text)
        updated = summary_repository.update_summary(db, summary_data)
        return updated
    else:
        return summary_repository.create_summary(db, summary_data)