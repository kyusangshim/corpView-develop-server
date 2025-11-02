from sqlalchemy import Column, Integer
from sqlalchemy.dialects.mysql import VARCHAR
from core.database import Base

class IndustryClassification(Base):
    __tablename__ = "industry_classification"
    __table_args__ = {"mysql_charset": "utf8", "mysql_collate": "utf8_general_ci"}

    id = Column(Integer, primary_key=True)

    code_1 = Column(VARCHAR(10))
    name_1 = Column(VARCHAR(100))
    
    code_2 = Column(VARCHAR(10))
    name_2 = Column(VARCHAR(100))
    
    code_3 = Column(VARCHAR(10))
    name_3 = Column(VARCHAR(100))
    
    code_4 = Column(VARCHAR(10))
    name_4 = Column(VARCHAR(100))
    
    code_5 = Column(VARCHAR(10))
    name_5 = Column(VARCHAR(200))