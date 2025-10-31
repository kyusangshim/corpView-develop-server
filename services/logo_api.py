# services/logo_api.py
import os
from urllib.parse import urlparse, parse_qs
from sqlalchemy.orm import Session
from models.company_overview import CompanyOverviews

LOGO_PUBLISHABLE_KEY = os.getenv("LOGO_PUBLISHABLE_KEY") or ""
BASE_IMG_URL = "https://img.logo.dev"


def _normalize_domain(hm_url: str) -> str:
    """
    hm_url에서 'http://', 'https://'와 'www.'를 제거하고
    순수 도메인(예: example.com)만 반환합니다.
    - 스킴이 없는 경우 기본으로 https:// 추가
    - domain에 최소 하나의 '.'이 없으면 유효하지 않은 도메인으로 간주하여 빈 문자열 반환
    - 도메인 앞뒤의 '-'는 제거
    """
    # 스킴이 없는 경우 https:// 추가
    if not hm_url.startswith(("http://", "https://")):
        hm_url = "https://" + hm_url

    parsed = urlparse(hm_url)
    domain = parsed.netloc.lower()
    # www. 제거
    if domain.startswith("www."):
        domain = domain[4:]
    # 유효성 검사: 도메인에 최소 하나의 점(.)이 있어야 함
    if "." not in domain:
        return ""
    # 도메인 앞뒤의 하이픈 제거
    domain = domain.strip("-")
    # 재검사: '.' 없으면 빈 문자열 반환
    if "." not in domain:
        return ""
    return domain


def fetch_logo_url(hm_url: str) -> str:
    domain = _normalize_domain(hm_url)
    if not domain or not LOGO_PUBLISHABLE_KEY:
        return ""
    return f"{BASE_IMG_URL}/{domain}?token={LOGO_PUBLISHABLE_KEY}&size=300&retina=true"


def update_company_logo(comp: CompanyOverviews, db: Session) -> str:
    """
    CompanyOverviews 인스턴스를 받아
    - logo 필드가 비어있거나 token=None 이면 새로 API 호출 후 업데이트
    - 그 외 이미 유효한 logo 값이 있으면 그대로 반환
    """
    if comp.logo:
        # URL 파싱해서 token 파라미터 값을 꺼내오기
        parsed = urlparse(comp.logo)
        params = parse_qs(parsed.query)
        token = params.get("token", [None])[0]

        # token 이 None 이 아니면(=유효한 key 로 이미 갱신된 URL 이면) 바로 반환
        if token and token.lower() != "none":
            return comp.logo

    # logo 가 비어있거나 token=None 인 경우, 새로 fetch
    logo_url = fetch_logo_url(comp.hm_url)
    if logo_url:
        comp.logo = logo_url
        db.add(comp)
        db.commit()
        db.refresh(comp)
    return comp.logo
