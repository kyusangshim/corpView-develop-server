# domains/companies/service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.companies import repository as company_repository


def add_favorite_count(db: Session, corp_code: int) -> int:
    """회사의 '좋아요' 수를 1 원자적으로 증가시킵니다."""
    rows_affected = company_repository.atomic_add_favorite_count(db, corp_code)
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="해당 기업을 찾을 수 없습니다.")

    db.commit()

    data = company_repository.get_company_by_code(db, corp_code)
    return data.favorite_count


def subtract_favorite_count(db: Session, corp_code: int) -> int:
    """회사의 '좋아요' 수를 1 원자적으로 감소시킵니다."""
    rows_affected = company_repository.atomic_subtract_favorite_count(db, corp_code)
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="기업을 찾을 수 없거나 '좋아요'가 0입니다.")

    db.commit()

    data = company_repository.get_company_by_code(db, corp_code)
    return data.favorite_count
