import os
from dotenv import load_dotenv

# .env 파일이 있다면 로드
load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = os.getenv("GROQ_URL")

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

DART_API = os.getenv("dart_api_key")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

SECRET_KEY = os.getenv("SECRET_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL")

LOGO_PUBLISHABLE_KEY = os.getenv("LOGO_PUBLISHABLE_KEY") or ""