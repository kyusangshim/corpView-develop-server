from pydantic import BaseModel
from typing import List, Dict

class NewsArticle(BaseModel):
    """
    개별 뉴스 기사 항목의 스키마
    """
    id: str
    title: str
    link: str
    pubDate: str 

class NewsResponse(BaseModel):
    """
    /news 엔드포인트의 응답 스키마
    """
    articles: List[NewsArticle]

# /news/all 엔드포인트의 응답 스키마 (타입 별칭 사용)
# 예: {"전체": [NewsArticle, ...], "채용": [NewsArticle, ...]}
AllNewsResponse = Dict[str, List[NewsArticle]]