from sqlalchemy import (
    Column, Integer, String, DateTime, 
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime
import pytz

SEOUL_TZ = pytz.timezone("Asia/Seoul")

class CachedNewsArticle(Base):
    __tablename__ = "cached_news_articles"
    __table_args__ = (
        UniqueConstraint("company_code", "category", "link", name="uq_company_category_link"),
        {"mysql_charset": "utf8mb4"}
    )
    
    id = Column(Integer, primary_key=True)
    
    company_code = Column(Integer, ForeignKey("company_overview.corp_code"), nullable=False, index=True)
    
    category = Column(String(50), nullable=False, index=True) 
    
    title = Column(String(512), nullable=False)
    link = Column(String(512), nullable=False) # 뉴스의 원본 링크
    pub_date = Column(DateTime(timezone=True), nullable=False) # Naver API가 제공하는 기사 발행일

    cached_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(SEOUL_TZ),
        onupdate=lambda: datetime.now(SEOUL_TZ),
        nullable=False
    )
    
    company = relationship("CompanyOverviews", back_populates="news")