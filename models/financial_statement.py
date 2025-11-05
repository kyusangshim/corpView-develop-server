from sqlalchemy import (
    Column, Integer, VARCHAR, BigInteger, JSON, 
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from core.database import Base

class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint("corp_code", "year", name="uq_company_year"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}
    )
    
    id = Column(Integer, primary_key=True)
    corp_code = Column(VARCHAR(8), ForeignKey("company_overview.corp_code"), nullable=False, index=True)
    
    # 2022, 2023, 2024...
    year = Column(Integer, nullable=False, index=True) 
    
    revenue = Column(BigInteger, nullable=True)          # 매출액
    operating_profit = Column(BigInteger, nullable=True) # 영업이익
    net_income = Column(BigInteger, nullable=True)       # 당기순이익
    total_assets = Column(BigInteger, nullable=True)     # 자산총계 (스키마에 따라 추가)
    total_equity = Column(BigInteger, nullable=True)     # 자본총계 (데이터에 따라 추가)
    
    ratios = Column(JSON, nullable=True) 

    company = relationship("CompanyOverviews", back_populates="financials")