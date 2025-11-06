# /clients/naver_news_client.py

import httpx
import html
from fastapi import HTTPException
from typing import List, Dict

from core.config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
from schemas.news import NewsArticle # 스키마는 재사용
from utils.utils import _make_id

async def fetch_news_by_query(query: str) -> List[NewsArticle]:
    """(L3) Naver News API를 비동기로 호출하고 Pydantic 모델로 반환합니다."""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="네이버 API 키가 없습니다.")
    
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&sort=sim"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status() 
            result = response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"네이버 API 호출 오류: {str(e)}")
        
    articles = []
    for item in result.get("items", []):
        title = html.unescape(item["title"].replace("<b>", "").replace("</b>", ""))
        articles.append(NewsArticle(
            id=_make_id(item["link"]),
            title=title,
            link=item["link"],
            pubDate=item["pubDate"]
        ))
    return articles