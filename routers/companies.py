from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from repository import company_repository
from services import company_service
from typing import List
from schemas.company import (
    CompanySearchResult,
    BestCompanyResult,
    CompanyByIndustry,
    FavoriteCountResult,
)

router = APIRouter()


"""(DB) 키워드로 회사를 검색합니다."""
@router.get("/search", response_model=List[CompanySearchResult])
def search_companies(keyword: str, db: Session = Depends(get_db)):
    companies = company_repository.search_companies_by_keyword(db, keyword)
    if not companies:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")
    return companies


"""(DB) 인기 기업 Top 3를 조회합니다."""
@router.get("/best", response_model=List[BestCompanyResult])
def get_best_companies(db: Session = Depends(get_db)):
    best_results = company_repository.get_best_companies(db, limit=3)
    if not best_results:
        return [] 
    return best_results


"""(DB) 산업 코드로 회사 목록을 조회합니다."""
@router.get("/by-industry", response_model=List[CompanyByIndustry])
def get_companies_by_industry(industry_code: int, db: Session = Depends(get_db)):
    result = company_repository.get_companies_by_industry_code(db, industry_code)
    if not result:
        return [] 
    return result


"""'좋아요'를 1 증가시킵니다. (Service 호출)"""
@router.post("/{corp_code}/favorite/add", response_model=FavoriteCountResult)
def add_favorites(corp_code: int, db: Session = Depends(get_db)):
    count = company_service.add_favorite_count(db, corp_code)
    return {"favorite_count": count}


"""'좋아요'를 1 감소시킵니다. (Service 호출)"""
@router.post("/{corp_code}/favorite/subtract", response_model=FavoriteCountResult)
def sub_favorites(corp_code: int, db: Session = Depends(get_db)):
    count = company_service.subtract_favorite_count(db, corp_code)
    return {"favorite_count": count}