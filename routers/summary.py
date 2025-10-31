from fastapi import APIRouter, Depends, HTTPException
from fastapi.logger import logger
from sqlalchemy.orm import Session
from database import get_db
from services.groq_service import summarize
from services.summary_crud import create_summary, get_recent_summary, update_summary
from schemas.summary import (
    SummaryCreate,
    SummaryOut,
    SummaryRequest,
    NewsArticle,
    RawFinancialEntry,
)
from typing import Dict, List

router = APIRouter(tags=["Summary"])


@router.post("", response_model=SummaryOut)
async def summarize_with_client_data(
    req: SummaryRequest, db: Session = Depends(get_db)
):
    # 1) 이미 저장된 요약이 있는지 확인
    existing = get_recent_summary(db, req.company_name)

    # 2) 전달받은 JSON → 텍스트 포맷 변환
    def format_financial(raw: Dict[str, RawFinancialEntry]) -> str:
        lines: List[str] = []
        # 년도 순 정렬
        for year in sorted(raw.keys()):
            entry = raw[year]
            lines.append(
                f"{year}년 자본총계 {entry.자본총계:,}원, 매출액 {entry.매출액:,}원, 영업이익 {entry.영업이익:,}원, 당기순이익 {entry.당기순이익:,}원"
            )
        return "\n".join(lines)

    def format_news(articles: List[NewsArticle]) -> str:
        return "\n".join(
            f"{a.title} ({a.pubDate.strftime('%Y-%m-%d %H:%M')}) - {a.link}"
            for a in articles
        )

    has_fin = req.financial
    has_news = req.news.get("채용")

    # 변경: 둘 다 없으면 모델 호출 없이 고정 메시지 반환
    if not has_fin and not has_news:
        summary_text = "AI요약을 생성하기 위한 정보를 찾을 수 없습니다."
    else:
        # 변경: 플레이스홀더 혹은 실제 텍스트 준비
        fin_text = (
            format_financial(req.financial)
            if has_fin
            else "재무정보가 제공되지 않았습니다."
        )
        news_text = (
            format_news(req.news.get("채용", []))
            if has_news
            else "채용 관련 뉴스정보가 제공되지 않았습니다."
        )

        # 3) Groq 요약 호출
        try:
            summary_text = await summarize(req.company_name, fin_text, news_text)
        except Exception as e:
            # 변경: Groq API 호출 에러(503 등) 처리
            logger.error(f"Groq API 호출 오류: {e.detail}")
            if e.status_code == 503:
                summary_text = (
                    "요약 서비스를 이용할 수 없습니다. 잠시 후 다시 시도해주세요."
                )
            else:
                # 기타 에러는 내부 서버 에러로 전환
                raise HTTPException(
                    status_code=500, detail="요약 처리 중 오류가 발생했습니다."
                )
    # 4) SummaryCreate 스키마로 데이터 준비
    summary_data = SummaryCreate(
        company_name=req.company_name, summary_text=summary_text
    )

    # 5) Upsert: 업데이트할 레코드가 있으면 update, 없으면 create
    if existing:
        updated = update_summary(db, req.company_name, summary_text)
        if updated:
            return updated
        # (혹시 update 실패 시) 새로 생성
        return create_summary(db, summary_data)
    else:
        return create_summary(db, summary_data)
