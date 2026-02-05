# /repository/news_repository.py

from sqlalchemy.orm import Session
from models.cached_news_article import CachedNewsArticle
from domains.news.schema import NewsArticle # Pydantic 스키마
from typing import Dict, Any, List
from datetime import datetime
import pytz
from email.utils import parsedate_to_datetime # 1. 날짜 파서 임포트

SEOUL_TZ = pytz.timezone("Asia/Seoul")

def get_cached_news_by_code(db: Session, corp_code: str) -> List[CachedNewsArticle]:
    """L2(RDB)에서 특정 회사의 모든 캐시된 뉴스를 조회합니다. (Fallback 용)"""
    return (
        db.query(CachedNewsArticle)
        .filter(CachedNewsArticle.corp_code == corp_code)
        .all()
    )

def upsert_news_articles(db: Session, corp_code: str, news_data: Dict[str, List[Dict]]):
    """
    L3(Naver)에서 가져온 새 데이터를 L2(RDB)에 덮어씁니다.
    (이전 캐시를 삭제하고 새로 삽입)
    """
    corp_code = "00" + corp_code if len(corp_code) == 6 else corp_code
    
    # 1. (Delete) L2의 기존 뉴스 캐시를 모두 삭제
    db.query(CachedNewsArticle).filter(CachedNewsArticle.corp_code == corp_code).delete(
        synchronize_session=False
    )
    
    now = datetime.now(SEOUL_TZ)
    
    # 2. (Insert) L3의 새 데이터를 L2에 삽입
    new_articles = []
    for category, articles in news_data.items():
        for article_dict in articles:
            # Pydantic 모델로 파싱/검증 (dict -> NewsArticle)
            article_model = NewsArticle.parse_obj(article_dict)

            try:
                dt_object = parsedate_to_datetime(article_dict['pubDate'])
            except Exception:
                dt_object = now # 파싱 실패 시 현재 시간으로 대체

            new_articles.append(
                CachedNewsArticle(
                    corp_code=corp_code,
                    category=category,
                    title=article_model.title,
                    link=str(article_model.link), # Pydantic HttpUrl을 str로 변환
                    pub_date=dt_object,
                    cached_at=now,
                )
            )
    
    db.add_all(new_articles)
    
    # 3. 트랜잭션은 Service 계층에서 commit/rollback 관리 (여기서는 안 함)