from sqlalchemy import Column, Text, TIMESTAMP, Integer
from sqlalchemy.dialects.mysql import VARCHAR
from core.database import Base


class CompanyOverviews(Base):
    __tablename__ = "company_overview"
    __table_args__ = {"mysql_charset": "utf8", "mysql_collate": "utf8_general_ci"}

    corp_code = Column(VARCHAR(8), primary_key=True)
    corp_name = Column(VARCHAR(255))
    corp_cls = Column(VARCHAR(10))
    adres = Column(Text)
    hm_url = Column(Text)
    induty_code = Column(VARCHAR(20))
    induty_name = Column(VARCHAR(255))
    est_dt = Column(VARCHAR(8))
    favorite_count = Column(Integer, default=0)
    logo = Column(VARCHAR(2048), default="", nullable=False)
