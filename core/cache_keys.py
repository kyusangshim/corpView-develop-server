# core/cache_keys.py

def details_info_key(name: str) -> str:
    return f"details:info:{name}"

def details_financials_key(corp_code: str) -> str:
    return f"details:financials:{corp_code}"

def details_news_key(name: str) -> str:
    return f"details:news:{name}"

def details_summary_key(name: str) -> str:
    return f"details:summary:{name}"

def lock_key(prefix: str, identifier: str) -> str:
    return f"details:lock:{prefix}:{identifier}"
