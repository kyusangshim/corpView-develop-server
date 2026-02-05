from pydantic import BaseModel, Field, HttpUrl, field_validator
from datetime import datetime
from typing import Dict, List, Optional


class SummaryBase(BaseModel):
    company_name: str


class SummaryCreate(SummaryBase):
    summary_text: str


class NewsArticle(BaseModel):
    id: str
    title: str
    link: HttpUrl  # 기존 url → link로 이름 변경
    pubDate: str  # string 형태로 와도 자동 파싱됨


class Ratio(BaseModel):
    영업이익률: float
    순이익률: float
    ROE: float


class RawFinancialEntry(BaseModel):
    매출액: int
    영업이익: int
    당기순이익: int
    자산총계: int
    자본총계: int
    ratio: Optional[Ratio] = None

    @field_validator("ratio", mode="before")
    def normalize_ratio(cls, v: any) -> Optional[Ratio]:
        # ratio가 없거나 빈 dict인 경우 None으로 대체
        if not v or (isinstance(v, dict) and not v):
            return None
        return v


class SummaryRequest(BaseModel):
    company_name: str = Field(..., description="기업 이름")
    financial: Dict[str, RawFinancialEntry] = Field(
        default_factory=dict
    )  # ex: [{"year": "2022", "revenue": 1000000, "operatingProfit": 200000, "netIncome": 150000}, ...]
    news: Dict[str, List[NewsArticle]] = Field(
        default_factory=dict
    )  # ex: {"전체": [{"id": "1", "title": "뉴스 제목", "link": "https://example.com/news1", "pubDate": "2023-10-01T12:00:00"}]}

    @field_validator("financial", mode="before")
    def normalize_financial(cls, v: any) -> Dict[str, RawFinancialEntry]:
        # {message: ...} or non-dict → 빈 dict
        if not isinstance(v, dict) or "message" in v:
            return {}
        cleaned: Dict[str, any] = {}
        # 필수 키와 값이 모두 존재하고, None이 아닐 경우만 필터
        required = ["자본총계", "매출액", "영업이익", "당기순이익"]
        for year, entry in v.items():
            if isinstance(entry, dict) and all(
                k in entry and entry.get(k) is not None for k in required
            ):
                cleaned[year] = entry
        return cleaned


class SummaryOut(SummaryBase):
    id: int
    summary_text: str
    created_at: datetime
    updated_at: datetime  # ← 추가

    class Config:
        orm_mode = True
