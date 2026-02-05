from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from domains.companies.model import CompanyOverviews

def get_company_by_name_exact(db: Session, name: str) -> CompanyOverviews | None:
    """이름으로 정확히 1개의 회사 정보를 조회합니다."""
    return (
        db.query(CompanyOverviews)
        .filter(CompanyOverviews.corp_name == name)
        .first()
    )

def get_company_by_code(db: Session, corp_code: int) -> CompanyOverviews | None:
    """회사 코드로 1개의 회사 정보를 조회합니다."""
    # PK 조회의 경우 .get()이 더 효율적입니다.
    return db.query(CompanyOverviews).get(corp_code) 


def atomic_add_favorite_count(db: Session, corp_code: int) -> int:
    """'좋아요' 수를 원자적으로 증가시켜, Race Condition 방지합니다."""
    result = (
        db.query(CompanyOverviews)
        .filter(CompanyOverviews.corp_code == corp_code)
        .update(
            {"favorite_count": CompanyOverviews.favorite_count + 1},
            synchronize_session=False
        )
    )
    return result

def atomic_subtract_favorite_count(db: Session, corp_code: int) -> int:
    """'좋아요' 수를 원자적으로 감소시켜, Race Condition 방지합니다."""
    result = (
        db.query(CompanyOverviews)
        .filter(
            CompanyOverviews.corp_code == corp_code,
            CompanyOverviews.favorite_count > 0 
        )
        .update(
            {"favorite_count": CompanyOverviews.favorite_count - 1},
            synchronize_session=False
        )
    )
    return result


def search_companies_by_keyword(db: Session, keyword: str) -> list[CompanyOverviews]:
    """키워드(ilike)로 여러 회사를 검색합니다."""
    return (
        db.query(CompanyOverviews)
        .filter(CompanyOverviews.corp_name.ilike(f"%{keyword}%"))
        .order_by(CompanyOverviews.corp_name.asc())
        .all()
    )

def get_best_companies(db: Session, limit: int = 3) -> list[CompanyOverviews]:
    """좋아요(favorite_count) 순으로 상위 N개 회사를 조회합니다."""
    return (
        db.query(CompanyOverviews)
        .order_by(CompanyOverviews.favorite_count.desc())
        .limit(limit)
        .all()
    )

def get_companies_by_industry_code(db: Session, industry_code: int) -> list[CompanyOverviews]:
    return (
        db.query(CompanyOverviews)
        .filter(CompanyOverviews.induty_code.like(f"{industry_code}%"))
        .all()
    )