# services/summary_crud.py

from sqlalchemy.orm import Session
from models.summary import Summary
from schemas.summary import SummaryCreate
from datetime import datetime
import pytz

SEOUL_TZ = pytz.timezone("Asia/Seoul")

def create_summary(db: Session, data: SummaryCreate) -> Summary:
    db_obj = Summary(**data.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_recent_summary(db: Session, company: str) -> Summary:
    return db.query(Summary).filter(Summary.company_name == company).first()


def update_summary(db: Session, data: SummaryCreate) -> Summary:
    """회사 이름이 일치하는 가장 최신 요약을 찾아 텍스트만 갱신."""
    db_obj = (
        db.query(Summary)
        .filter(Summary.company_name == data.company_name)
        .first()
    )
    if not db_obj:
        return None
    db_obj.summary_text = data.summary_text
    db.commit()
    db.refresh(db_obj)
    return db_obj


def upsert_summary(db: Session, data: SummaryCreate):
    """
    (수정) 요약 데이터를 Upsert(Update or Insert)합니다.
    (COMMIT은 서비스 계층이 담당합니다.)
    """
    db_obj = get_recent_summary(db, data.company_name)
    
    if db_obj:
        # (Update)
        db_obj.summary_text = data.summary_text
        db_obj.updated_at = datetime.now(SEOUL_TZ)
    else:
        # (Insert)
        db_obj = Summary(**data.dict())
        db.add(db_obj)
    
    # [!] db.commit()을 여기서 호출하지 않습니다.
    # [!] db.refresh()도 서비스 계층에서 필요시 호출합니다.
