from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


# 공통 필드
class UserBase(BaseModel):
    email: str
    name: str


# 사용자 생성 시 입력
class UserCreate(UserBase):
    oauth_provider: str
    oauth_sub: str
    preferences: Optional[List[str]] = Field(default_factory=list)
    favorites: Optional[List[int]] = Field(default_factory=list)


# 선호 카테고리 업데이트용
class PreferencesUpdate(BaseModel):
    preferences: List[str]


# 관심기업 추가용
class FavoriteCreate(BaseModel):
    company_id: int


# 사용자 업데이트 시 입력
class UserUpdate(BaseModel):
    preferences: Optional[List[str]] = None
    favorites: Optional[List[int]] = None


# 응답용 스키마
class UserOut(UserBase):
    id: int
    oauth_provider: str
    oauth_sub: str
    preferences: List[str]
    favorites: List[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IndustryCategoryNode(BaseModel):
    id: int
    name_1: Optional[str]
    code_1: Optional[str]
    name_2: Optional[str]
    code_2: Optional[str]
    name_3: Optional[str]
    code_3: Optional[str]
    name_4: Optional[str]
    code_4: Optional[str]
    name_5: Optional[str]
    code_5: Optional[str]

    class Config:
        from_attributes = True
