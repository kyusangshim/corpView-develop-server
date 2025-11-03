from fastapi import HTTPException
from sqlalchemy.orm import Session
from repository import company_repository

def add_favorite_count(db: Session, corp_code: int) -> int:
    """회사의 '좋아요' 수를 1 증가시킵니다."""
    data = company_repository.get_company_by_code(db, corp_code)
    if not data:
        raise HTTPException(status_code=404, detail="해당 기업을 찾을 수 없습니다.")
    
    data.favorite_count += 1
    db.commit()
    db.refresh(data)
    return data.favorite_count


def subtract_favorite_count(db: Session, corp_code: int) -> int:
    """회사의 '좋아요' 수를 1 감소시킵니다."""
    data = company_repository.get_company_by_code(db, corp_code)
    if not data:
        raise HTTPException(status_code=404, detail="해당 기업을 찾을 수 없습니다.")
    
    if data.favorite_count > 0:
        data.favorite_count -= 1
        db.commit()
        db.refresh(data)
    
    return data.favorite_count