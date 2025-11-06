# /clients/dart_api_client.py

import httpx
from core.config import DART_API
from fastapi import HTTPException

async def fetch_financial_raw(code: str) -> dict:
    """(L3) DART API 원본(raw) 데이터를 비동기로 호출합니다."""
    code = "00" + code if len(code) == 6 else code
    url = f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json?crtfc_key={DART_API}&corp_code={code}&bsns_year=2024&reprt_code=11011"
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status() # HTTP 오류 체크
            data = response.json()
            if "list" not in data:
                raise HTTPException(status_code=404, detail="DART 재무 데이터가 없습니다.")
            return data
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"DART API 오류: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DART API 호출 중 오류: {str(e)}")