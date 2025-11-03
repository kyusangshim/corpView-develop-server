from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from repository import industry_repository, user_repository
from schemas.user import IndustryCategoryNode # 스키마를 사용하셨네요. 좋습니다.
from typing import List

router = APIRouter()

@router.get("", response_model=List[IndustryCategoryNode])
def get_all_industries(db: Session = Depends(get_db)):
    """(DB) 전체 산업 분류 목록을 조회합니다."""
    industries = industry_repository.get_all_industries(db)
    # Pydantic 모델(스키마)로 자동 변환
    return [IndustryCategoryNode.from_orm(ind) for ind in industries]

@router.get("/code")
def get_industry_code_from_name(name: str, level: int, db: Session = Depends(get_db)):
    """(DB) 산업 이름과 레벨로 산업 코드를 조회합니다."""
    code = industry_repository.get_industry_code_by_name_and_level(db, name, level)
    if not code:
        raise HTTPException(status_code=404, detail="산업 코드를 찾을 수 없습니다.")
    return {"code": code}

@router.get("/user-preferences")
def get_user_industry_preferences(user_id: int, db: Session = Depends(get_db)):
    """(DB) 사용자의 관심 산업 코드를 조회합니다."""
    preferences = user_repository.get_user_preferences_by_id(db, user_id)
    if not preferences:
        raise HTTPException(status_code=404, detail="사용자의 관심 산업 정보를 찾을 수 없습니다.")
    return preferences