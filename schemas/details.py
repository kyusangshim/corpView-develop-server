# /schemas/details.py

from pydantic import BaseModel
from typing import Dict
from schemas.company import CompanyInfo
from schemas.news import AllNewsResponse
from schemas.summary import RawFinancialEntry

class CompanyDetailResponse(BaseModel):
    """
    /details/company-details 엔드포인트의 
    최종 통합 응답 스키마
    """
    company_info: CompanyInfo
    financial_data: Dict[str, RawFinancialEntry]
    news_data: AllNewsResponse
    ai_summary: str