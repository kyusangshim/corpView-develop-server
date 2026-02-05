from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from datetime import datetime
import pytz
from core.database import Base

SEOUL_TZ = pytz.timezone("Asia/Seoul")

class Summary(Base):
    __tablename__ = "summaries"
    __table_args__ = (
        # 1) company_name 유니크 제약 추가
        UniqueConstraint("company_name", name="uq_summaries_company_name"),
        {
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
    )

    id = Column(Integer, primary_key=True, index=True)
    # 2) unique=True 옵션 추가 (ORM 차원에서도 명시)
    company_name = Column(String(255), index=True, nullable=False, unique=True)
    summary_text = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SEOUL_TZ),
        nullable=False
    )
    # 3) (선택) 갱신 시점 관리용 updated_at 컬럼 추가
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SEOUL_TZ),
        onupdate=lambda: datetime.now(SEOUL_TZ),
        nullable=False
    )
