from pydantic import BaseModel, Field
from typing import Optional

class CompanyBase(BaseModel):
    corp_code: int
    corp_name: str
    logo: Optional[str] = None

class CompanyInfo(CompanyBase):
    adres: Optional[str] = None
    corp_cls: Optional[str] = None
    est_dt: Optional[str] = None
    hm_url: Optional[str] = None
    induty_name: Optional[str] = None

    class Config:
        from_attributes = True

class CompanySearchResult(CompanyBase):
    hm_url: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True 

class BestCompanyResult(CompanyBase):
    favorite_count: Optional[int] = 0
    category: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class CompanyByIndustry(CompanyBase):
    induty_code: Optional[str] = None
    induty_name: Optional[str] = None

    class Config:
        from_attributes = True

class FavoriteCountResult(BaseModel):
    favorite_count: int
