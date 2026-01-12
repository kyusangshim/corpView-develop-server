# 기업 분석 웹 애플리케이션 (백엔드)

![License](https://img.shields.io/badge/license-MIT-blue.svg)

Company Analysis App의 백엔드 API 서버입니다.  
FastAPI 기반으로 RESTful API를 제공하며, 기업 재무 데이터 조회, 뉴스 수집·요약, 사용자 인증·즐겨찾기 기능 등을 지원합니다.

## 목차
- [기업 분석 웹 애플리케이션 백엔드](#기업-분석-웹-애플리케이션-백엔드)
  - [목차](#목차)
  - [기술 스택](#기술-스택)
  - [프로젝트 구조](#프로젝트-구조)
  - [설치 및 실행](#설치-및-실행)
    - [1. 저장소 클론](#1-저장소-클론)
    - [2. 가상환경 생성 및 활성화](#2-가상환경-생성-및-활성화)
    - [3. 의존성 설치](#3-의존성-설치)
    - [4. 서버 실행](#4-서버-실행)
  - [환경 변수](#환경-변수)
  - [주요 기능](#주요-기능)
  - [주요 엔드포인트](#주요-엔드포인트)
  - [데이터베이스 스키마 예시](#데이터베이스-스키마-예시)
  - [외부 API 연동](#외부-api-연동)
  - [향후 개발 계획](#향후-개발-계획)
  - [라이센스](#라이센스)

---

## 기술 스택
- **Framework**: FastAPI  
- **언어**: Python 3.10+  
- **데이터베이스**: MySQL (SQLAlchemy)
- **캐시**: Redis
- **ASGI 서버**: Uvicorn 
- **인증**: OAuth2 (python-jose)
- **AI**: Groq AI

---

## 프로젝트 구조
```
corpView-develop-server/
├── core/                   # 설정 및 공통 모듈
│   ├── cache.py            # Redis 캐시 설정
│   ├── config.py           # 환경 변수 로드
│   └── database.py         # DB 연결 및 엔진 설정
├── models/                 # SQLAlchemy ORM 모델 정의
│   ├── user.py
│   ├── summary.py
│   ├── industry_classification.py
│   └── company_overview.py
├── repository/             # DB CRUD 로직 (Repository 패턴)
│   ├── user_repository.py
│   ├── company_repository.py
│   └── industry_repository.py
├── routers/                # API 엔드포인트 라우터
│   ├── auth.py             # 인증 관련
│   ├── users.py            # 유저 정보
│   ├── companies.py        # 기업 정보
│   ├── industries.py       # 산업군 정보
│   └── details_all.py      # 기업 상세 분석 (Final)
├── schemas/                # Pydantic 데이터 검증 스키마
│   ├── user.py
│   ├── company.py
│   ├── details.py
│   └── summary.py
├── services/               # 비즈니스 로직 및 외부 API 통신
│   ├── groq_service.py     # AI 요약 서비스
│   ├── dart_api_service.py # DART 데이터 연동
│   └── news_service.py     # 네이버 뉴스 연동
├── utils/                  # 공통 유틸리티 함수
├── main.py                 # 앱 초기화 및 라우터 등록
└── requirements.txt        # 의존성 목록
```

---

## 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/kyusangshim/corpview-develop-server.git
cd company-analysis-app-server
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 서버 실행
```bash
uvicorn app.main:app --reload
```

---

## 환경 변수

프로젝트 루트에 `.env` 파일을 생성하고, 다음 값을 설정하세요:
```env
# Database
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<database>

# Security & Session
SECRET_KEY=<your_secret_key>
FRONTEND_URL=http://localhost:3000

# AI (Groq)
GROQ_API_KEY=<your_api_key>
GROQ_URL=<api_url>

# External APIs
dart_api_key=<your_dart_key>
NAVER_CLIENT_ID=<your_id>
NAVER_CLIENT_SECRET=<your_secret>

# OAuth (Google)
GOOGLE_CLIENT_ID=<your_id>
GOOGLE_CLIENT_SECRET=<your_secret>

# Cache
REDIS_URL=redis://127.0.0.1:6379/0

# Others
LOGO_PUBLISHABLE_KEY=<your_key>
```

---

## 주요 기능
- **기업 재무정보 조회**  
  DART Open API 연동을 통해 기업별 재무제표 및 개황 정보 제공  
- **뉴스 수집 & 카테고리별 검색**  
  Naver News API를 활용해 기업 관련 최신 뉴스 조회  
- **AI 요약 생성**  
  Groq API(gemma2-9b-it) 기반으로 기업 요약 보고서 자동 생성  
- **사용자 인증 & 권한 관리**  
  OAuth2(Google) 로그인, JWT 발급/검증  
- **관심기업·선호카테고리 관리**  
  사용자별 즐겨찾기 CRUD, 산업군·기업규모 기반 카테고리 필터  
- **인기·추천 기업**  
  전체 사용자 데이터 기반 TOP3 인기 기업, 개인 맞춤 추천 리스트  

---

## 주요 엔드포인트
main.py에 정의된 주요 라우터 경로는 다음과 같습니다:
- `/auth`: OAuth 로그인 및 인증
- `/users`: 유저 정보 관리
- `/companies`: 기업 검색 및 목록 조회
- `/industries`: 산업군 분류 및 추천
- `/details-final`: 기업별 AI 요약 및 상세 정보 제공

---

## 데이터베이스 스키마 예시
- `users`: 사용자 관련 데이터 정의
- `token`: JWT 의존성 토큰 관련
- `summary`: AI 요약관련 데이터 정의
  
```sql
-- users table
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL UNIQUE,
  full_name VARCHAR(100),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- summary table
CREATE TABLE summary (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  company_name VARCHAR(100),
  summary_text TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 외부 API 연동
- **DART API**: 기업 재무 데이터
- **Naver 뉴스 API**: 최신 뉴스
- **Groq API**: 기업 정보 AI 요약 제공
- **Logo.dev**: 기업로고 생성

---

## 향후 개발 계획
- 추가 비즈니스 로직 및 예외 처리 강화   
- 실시간 알림 푸시 서비스 연동  
- Kubernetes 기반 무중단 배포 환경 구축 

---
  
## 라이센스

MIT © Company Analysis App
