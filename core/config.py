import os
from dotenv import load_dotenv

# .env 파일이 있다면 로드
load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY") # (예시)
# NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID") # (예시)