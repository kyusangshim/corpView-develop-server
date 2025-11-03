
from typing import Dict, List
import hashlib
from schemas.summary import (
    NewsArticle,
    RawFinancialEntry,
)


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