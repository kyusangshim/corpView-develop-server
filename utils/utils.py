
from typing import Dict, List, Any
import hashlib
from schemas.summary import (
    NewsArticle,
    RawFinancialEntry,
)
from models.financial_statement import FinancialStatement
from models.cached_news_article import CachedNewsArticle



# summary 헬퍼 함수
def _format_financial(raw: Dict[str, RawFinancialEntry]) -> str:
    lines: List[str] = []
    for year in sorted(raw.keys()):
        entry = raw[year]
        lines.append(
            f"{year}년 자본총계 {entry.자본총계:,}원, 매출액 {entry.매출액:,}원, 영업이익 {entry.영업이익:,}원, 당기순이익 {entry.당기순이익:,}원"
        )
    return "\n".join(lines)

def _format_news(articles: List[NewsArticle]) -> str:
    return "\n".join(
        f"{a.title} ({a.pubDate.strftime('%Y-%m-%d %H:%M')}) - {a.link}"
        for a in articles
    )


# ... (다른 임포트들) ...
from datetime import datetime # 1. datetime 임포트
from email.utils import parsedate_to_datetime # 2. RFC 2822 형식 파싱용 임포트

def _format_news_for_groq(articles: List[NewsArticle]) -> str:
    """Groq API에 보낼 뉴스 텍스트를 포맷합니다. (날짜 파싱 추가)"""
    lines = []
    for a in articles:
        try:
            # 1. Naver API의 날짜 문자열(str)을 datetime 객체로 파싱합니다.
            # 예: "Mon, 03 Nov 2025 11:07:00 +0900" -> datetime 객체
            dt = parsedate_to_datetime(a.pubDate)
            
            # 2. 원하는 형식으로 다시 문자열로 포맷합니다.
            formatted_date = dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            # 3. 파싱에 실패할 경우 (예외 처리) 원본 문자열을 그대로 사용합니다.
            formatted_date = a.pubDate 
            
        lines.append(f"{a.title} ({formatted_date}) - {a.link}")
    return "\n".join(lines)


# news 헬퍼 함수
def _make_id(text: str) -> str:
    """링크 텍스트로 고유 ID를 생성합니다."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# dart api 헬퍼 함수
def clean(val):
    if not isinstance(val, str):
        return None
    text = val.strip()
    if not text or text == "-":
        return None
    num_str = text.replace(",", "")
    try:
        return int(num_str)
    except ValueError:
        return None


def normalize(name):
    return name.split("(")[0].strip()


def calculate_ratios(res):
    sales = res.get("매출액")
    op = res.get("영업이익")
    net = res.get("당기순이익")
    equity = res.get("자본총계")
    ratios = {}
    if sales and sales != 0:
        ratios["영업이익률"] = round(op / sales * 100, 2) if op else None
        ratios["순이익률"] = round(net / sales * 100, 2) if net else None
    if equity and equity != 0:
        ratios["ROE"] = round(net / equity * 100, 2) if net else None
    return ratios



# financials & news 헬퍼함수
def _format_financials_from_orm(orm_list: List[FinancialStatement]) -> Dict[str, Any]:
    result = {}
    for item in orm_list:
        result[str(item.year)] = {
            "매출액": item.revenue,
            "영업이익": item.operating_profit,
            "당기순이익": item.net_income,
            "자산총계": item.total_assets,
            "자본총계": item.total_equity,
            "ratio": item.ratios,
        }
    return result

def _format_news_from_orm(orm_list: List[CachedNewsArticle]) -> Dict[str, List[Dict]]:
    result = {}
    for item in orm_list:
        if item.category not in result:
            result[item.category] = []
        result[item.category].append({
            "id": _make_id(item.link), # (naver_service의 _make_id 임포트 필요)
            "title": item.title,
            "link": item.link,
            "pubDate": item.pub_date.isoformat(),
        })
    return result