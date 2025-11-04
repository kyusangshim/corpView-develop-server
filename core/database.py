from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. config.py에서 설정 값을 가져옴
from core.config import DATABASE_URL 

# 2. engine 생성 시 설정 값 사용
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. get_db 함수는 그대로 유지
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()