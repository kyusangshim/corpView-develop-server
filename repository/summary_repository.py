# services/summary_crud.py

from sqlalchemy.orm import Session
from models.summary import Summary
from schemas.summary import SummaryCreate


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
