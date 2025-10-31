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
- **ASGI 서버**: Uvicorn 
- **인증**: OAuth2 (python-jose)  

---

## 프로젝트 구조
```
company-analysis-app-server/
├── models/                         # 데이터베이스 ORM 모델 정의
│   ├── user.py
│   ├── summary.py
│   └── company_overview.py
├── routers/                        # API 라우터
│   ├── auth.py
│   ├── dart_search.py
│   ├── dart.py
│   ├── naver_news.py
│   ├── summary.py
│   └── users.py
├── schemas/                        # 데이터 검증 스키마 정의
│   ├── user.py
│   ├── summary.py
│   └── token.py
├── services/                       # 외부 API 및 기타함수 호출
│   ├── groq_service.py
│   ├── logo_api.py
│   └── summary_crud.py
├── database.py                     # 데이터베이스 연결 및 세션 관리
├── main.py                         # FastAPI 애플리케이션 설정 및 라우터 등록
├── requirements.txt                # Python 필요 패키지 라이브러리 목록
├── .env                            # 환경변수 셋팅
├── 산업코드.csv                     # 산업코드 분류 CSV
└── README.md
```

---

## 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/company-analysis-app/company-analysis-app-server.git
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
# 데이터베이스
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<database>

# CORS 허용
FRONTEND_URL=http://localhost:3000

# 보안
SECRET_KEY=<your_secret_key>

# OAuth2 (Google)
GOOGLE_CLIENT_ID=<your_google_client_id>
GOOGLE_CLIENT_SECRET=<your_google_client_secret>

# 외부 API 키
DART_API_KEY=<your_dart_api_key>
NAVER_CLIENT_ID=<your_naver_client_id>
NAVER_CLIENT_SECRET=<your_naver_client_secret>
GROQ_API_KEY=<your_groq_api_key>

# 로고 서비스
LOGO_PUBLISHABLE_KEY=<your_logo_publishable_key>
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

- `/auth`: OAuth 로그인 및 인증
- `/dart`: 기업 재무정보 검색
- `/dart_search`: 기업 개황정보 검색
- `/users`: 유저 정보 관리
- `/naver`: 기업 뉴스정보 검색
- `/summary`: 기업 AI요약 데이터 생성

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
- 캐싱(Redis) 도입으로 API 응답 성능 개선  
- 실시간 알림 푸시 서비스 연동  
- Kubernetes 기반 무중단 배포 환경 구축 

---
  
## 라이센스

MIT © Company Analysis App
