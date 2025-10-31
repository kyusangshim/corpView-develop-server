# routers/dart_search.py
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from models.user_industry_favorite import UserIndustryFavorite
from models.industry_classification import IndustryClassification
from models.company_overview import CompanyOverviews
from schemas.user import IndustryCategoryNode
from database import get_db
from sqlalchemy.sql.expression import func
from services.logo_api import update_company_logo
from typing import List
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()


@router.get("/getIndustry")
def get_industry_code_from_name(name: str, level: int, db: Session = Depends(get_db)):
    level += 1
    name_column = getattr(IndustryClassification, f"name_{level}")
    code_column = getattr(IndustryClassification, f"code_{level}")

    industry_row = (
        db.query(code_column)
        .filter(name_column == name)
        .first()
    )

    if not industry_row:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")

    return {"code": industry_row[0]}


@router.get("/getIndustryCode")
def get_industry_code(user_id: int, db: Session = Depends(get_db)):
    favorite = (
        db.query(UserModel.preferences)
        .filter(UserModel.id == user_id)
        .first()
    )

    if not favorite:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")

    return favorite.preferences



@router.get("/getData")
def get_data(industry_code: int, db: Session = Depends(get_db)):
    result = (
        db.query(CompanyOverviews)
        .filter(CompanyOverviews.induty_code.like(f"{industry_code}%"))
        .order_by(func.rand())
        .all()
    )

    if not result:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")

    result_list = []
    for row in result:
        row.logo = update_company_logo(row, db)
        result_list.append({
            "corp_code": row.corp_code,
            "corp_name": row.corp_name,
            "induty_code": row.induty_code,
            "induty_name": row.induty_name,
            "logo": row.logo,
        })

    return result_list



# 5) 산업군 목록 조회
@router.get("/industries", response_model=List[IndustryCategoryNode])
def get_industries(db: Session = Depends(get_db)):
    industries = db.query(IndustryClassification).all()
    return [IndustryCategoryNode.from_orm(ind) for ind in industries]


# 6) 관심 산업군 추가
@router.post("/industry-favorites", response_model=List[int])
def add_industry_favorites(
    industry_ids: List[int],
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    for industry_id in industry_ids:
        exists = db.query(UserIndustryFavorite).filter_by(
            user_id=current_user.id, industry_id=industry_id
        ).first()
        if not exists:
            db.add(UserIndustryFavorite(user_id=current_user.id, industry_id=industry_id))
    db.commit()
    rows = db.query(UserIndustryFavorite).filter_by(user_id=current_user.id).all()
    return [row.industry_id for row in rows]

# 7) 관심 산업군 제거
@router.delete("/industry-favorites/{industry_id}", response_model=List[int])
def remove_industry_favorite(
    industry_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    row = db.query(UserIndustryFavorite).filter_by(
        user_id=current_user.id, industry_id=industry_id
    ).first()
    if row:
        db.delete(row)
        db.commit()
    rows = db.query(UserIndustryFavorite).filter_by(user_id=current_user.id).all()
    return [row.industry_id for row in rows]

@router.post("/users/industry-favorites")
def add_industry_favorite(code: str, db: Session = Depends(get_db), user: UserModel = Depends(get_current_user)):
    # code가 일치하는 industry를 찾는다
    industry = db.query(IndustryClassification).filter(
        (IndustryClassification.code_2 == code) |
        (IndustryClassification.code_3 == code) |
        (IndustryClassification.code_4 == code) |
        (IndustryClassification.code_5 == code)
    ).first()

    if not industry:
        raise HTTPException(status_code=404, detail="해당 코드의 산업군이 존재하지 않습니다.")

    # 이미 등록되어 있으면 무시
    existing = db.query(UserIndustryFavorite).filter_by(
        user_id=user.id,
        industry_id=industry.id
    ).first()

    if existing:
        return {"message": "이미 등록된 관심 산업군입니다."}

    # 새로 추가
    favorite = UserIndustryFavorite(
        user_id=user.id,
        industry_id=industry.id
    )
    db.add(favorite)
    db.commit()

    return {"message": "관심 산업군 등록 완료"}

@router.get("/industry-favorites", response_model=List[int])
def get_industry_favorites(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    rows = db.query(UserIndustryFavorite).filter_by(user_id=current_user.id).all()
    return [row.industry_id for row in rows]