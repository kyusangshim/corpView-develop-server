from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime



class UserIndustryFavorite(Base):
    __tablename__ = "user_industry_favorite"
    __table_args__ = (
        UniqueConstraint("user_id", "industry_id", name="uniq_user_industry"),
        {"mysql_charset": "utf8", "mysql_collate": "utf8_general_ci"}
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, primary_key=True)
    industry_id = Column(Integer, ForeignKey("industry_classification.id"), nullable=False, primary_key=True)

    user = relationship("User", back_populates="favorites_industries")
    industry = relationship("IndustryClassification")