import httpx
import html
import asyncio
from fastapi import HTTPException
from typing import List, Dict

from core.config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
from schemas.news import NewsArticle # 1단계에서 만든 스키마
from utils.utils import _make_id

# 카테고리 목록은 이 서비스를 사용하는 곳에 두는 것이 좋습니다.
CATEGORIES = ["전체", "채용", "주가", "노사", "IT"]

async def fetch_news_by_query(query: str) -> List[NewsArticle]:
    """
    단일 쿼리로 Naver News API를 호출하고, 
    결과를 NewsArticle 스키마 리스트로 반환합니다.
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        # 서비스 단에서는 구체적인 예외를 발생시킵니다.
        raise HTTPException(
            status_code=500, 
            detail="NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경변수가 없습니다."
        )
    
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&sort=sim"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            # HTTP 오류 (4xx, 5xx) 발생 시 예외 발생
            response.raise_for_status() 
            result = response.json()
        
        except httpx.HTTPStatusError as e:
            # API 호출이 HTTP 상태 코드 오류로 실패한 경우
            raise HTTPException(
                status_code=e.response.status_code, 
                detail=f"네이버 API 호출 실패: {e.response.text}"
            )
        except Exception as e:
            # JSON 파싱 실패, 네트워크 오류 등 기타 예외
            raise HTTPException(
                status_code=500, 
                detail=f"네이버 API 응답 처리 중 오류: {str(e)}"
            )
        
    articles = []
    for item in result.get("items", []):
        title = html.unescape(item["title"].replace("<b>", "").replace("</b>", ""))
        link = item["link"]
        pubDate = item["pubDate"]
        
        # Pydantic 모델(스키마) 객체로 생성
        articles.append(NewsArticle(
            id=_make_id(link),
            title=title,
            link=link,
            pubDate=pubDate
        ))
    return articles

async def fetch_all_news_by_category(company: str) -> Dict[str, List[NewsArticle]]:
    """
    모든 카테고리의 뉴스를 asyncio.gather로 병렬 조회합니다.
    """
    tasks = []
    for cat in CATEGORIES:
        if cat == "전체":
            q = company
        else:
            q = f"{company} {cat}"
        # fetch_news_by_query 함수를 호출하는 task를 리스트에 추가
        tasks.append(fetch_news_by_query(q))
    
    # 모든 task를 병렬로 실행
    results = await asyncio.gather(*tasks)
    
    # 카테고리와 결과 리스트를 딕셔너리로 매핑하여 반환
    return {cat: news for cat, news in zip(CATEGORIES, results)}