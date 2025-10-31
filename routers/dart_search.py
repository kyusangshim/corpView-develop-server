# routers/dart_search.py
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from models.company_overview import CompanyOverviews
from database import get_db
from services.logo_api import update_company_logo

router = APIRouter()


@router.post("/")
def get_bords(keyword: str, db: Session = Depends(get_db)):
    companies = (
        db.query(CompanyOverviews)
        .filter(CompanyOverviews.corp_name.ilike(f"%{keyword}%"))
        .order_by(CompanyOverviews.corp_name.asc())
        .all()
    )

    if not companies:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")

    result_list = []
    for comp in companies:
        # 로고가 없으면 업데이트
        comp.logo = update_company_logo(comp, db)
        result_list.append(
            {
                "corp_code": comp.corp_code,
                "corp_name": comp.corp_name,
                "hm_url": comp.hm_url,
                "logo": comp.logo,
                "category": comp.induty_name,
            }
        )

    return result_list


@router.post("/bestCompanies")
def get_best_companies(db: Session = Depends(get_db)):
    best_results = (
        db.query(CompanyOverviews)
        .order_by(CompanyOverviews.favorite_count.desc())
        .limit(3)
        .all()
    )

    if not best_results:
        return {"message": "회사를 찾을 수 없습니다."}

    result_list = []
    for comp in best_results:
        # 로고가 없으면 업데이트
        comp.logo = update_company_logo(comp, db)
        result_list.append(
            {
                "corp_code": comp.corp_code,
                "corp_name": comp.corp_name,
                "favorite_count": comp.favorite_count,
                "logo": comp.logo,
                "category": comp.induty_name,
            }
        )

    return result_list
