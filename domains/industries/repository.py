from sqlalchemy.orm import Session
from models.industry_classification import IndustryClassification
from typing import List

def get_industry_code_by_name_and_level(db: Session, name: str, level: int) -> str | None:
    """산업 이름과 레벨로 산업 코드를 조회합니다."""
    level += 1
    name_column = getattr(IndustryClassification, f"name_{level}")
    code_column = getattr(IndustryClassification, f"code_{level}")

    industry_row = (
        db.query(code_column)
        .filter(name_column == name)
        .first()
    )
    return industry_row[0] if industry_row else None

def get_all_industries(db: Session) -> List[IndustryClassification]:
    """모든 산업 분류 목록을 조회합니다."""
    return db.query(IndustryClassification).all()