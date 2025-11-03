from fastapi import APIRouter, Query
from services import news_service
from schemas.news import NewsResponse, AllNewsResponse

# API 경로(prefix)를 /naver로 그룹화하는 것을 추천합니다.
router = APIRouter()

@router.get("/news", response_model=NewsResponse)
async def get_news(query: str = Query(...)):
    """
    (Service 호출) 단일 쿼리로 네이버 뉴스를 검색합니다.
    """
    articles_list = await news_service.fetch_news_by_query(query)
    return {"articles": articles_list}

@router.get("/news/all", response_model=AllNewsResponse)
async def get_all_news(company: str = Query(...)):
    """
    (Service 호출) 회사 이름으로 모든 카테고리의 뉴스를 병렬 조회합니다.
    """
    return await news_service.fetch_all_news_by_category(company)