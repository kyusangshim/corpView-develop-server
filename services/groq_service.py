import os
import httpx
from fastapi import HTTPException

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SYSTEM_PROMPT = [
    "You are a professional financial analyst and summarizer.",
    "입력 데이터:",
    "- 회사명 (company_name)",
    "- 재무정보: past 3년 매출(revenue), 영업이익(operatingProfit), 순이익(netIncome)",
    "- 뉴스: 채용 카테고리 기사 리스트(제목, 날짜, 링크)",
    "출력에는 반드시 다음을 포함하세요:",
    "1. 최근 3개년 재무지표의 상승세 혹은 하강세 분석",
    "2. 채용 관련 뉴스의 주요 이슈 요약",
    "출력 형식: 한국어, 5문장 이내로 간결하게",
    "**불필요한 특수문자 사용금지**",
]


async def summarize(company_name: str, fin_text: str, news_text: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [
                {"role": "system", "content": " ".join(SYSTEM_PROMPT)},
                {
                    "role": "user",
                    "content": (
                        f"회사: {company_name}\n\n" f"{fin_text}\n\n" f"{news_text}"
                    ),
                },
            ],
        }
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = await client.post(GROQ_URL, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Groq API error: {e.response.text}",
            )
        data = resp.json()
        return data["choices"][0]["message"]["content"]
