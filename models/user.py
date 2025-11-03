from sqlalchemy import Column, Integer, String, JSON, DateTime, UniqueConstraint
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime
import pytz

SEOUL_TZ = pytz.timezone("Asia/Seoul")
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("oauth_provider", "oauth_sub", name="uq_provider_sub"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    oauth_provider = Column(String(50), nullable=False)
    oauth_sub = Column(String(100), nullable=False)

    preferences    = Column(MutableList.as_mutable(JSON), default=list, nullable=False)
    favorites      = Column(MutableList.as_mutable(JSON), default=list, nullable=False)
    
    # 생성 시각 (한국 시각)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SEOUL_TZ),
        nullable=False,
    )
    # 수정 시각 (한국 시각)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(SEOUL_TZ),
        onupdate=lambda: datetime.now(SEOUL_TZ),
        nullable=False,
    )
