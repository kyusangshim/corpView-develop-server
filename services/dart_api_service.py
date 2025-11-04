# import requests as rq -> 삭제
import httpx # <-- 1. httpx 임포트
import pandas as pd
from core.config import DART_API
from utils.utils import clean, normalize, calculate_ratios

async def fetch_and_process_financials(code: str) -> dict:
    """DART API로 재무 정보를 (비동기로) 가져오고 Pandas로 가공합니다."""
    code = "00" + code if len(code) == 6 else code
    url = f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json?crtfc_key={DART_API}&corp_code={code}&bsns_year=2024&reprt_code=11011"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status() # HTTP 오류 체크
            data = response.json()
        except httpx.HTTPStatusError as e:
            return {"message": f"DART API 오류: {e.response.status_code}"}
        except Exception as e:
            return {"message": f"DART API 호출 중 오류: {str(e)}"}

    if "list" not in data:
        return {"message": "데이터가 없습니다."}

    df = pd.DataFrame(data["list"])
    if "fs_div" not in df.columns:
        return {"message": "'fs_div' 정보가 없습니다."}

    if (df["fs_div"] == "CFS").any():
        df = df[df["fs_div"] == "CFS"]
    elif (df["fs_div"] == "OFS").any():
        df = df[df["fs_div"] == "OFS"]
    else:
        return {"message": "CFS/OFS 기준 데이터가 없습니다."}

    keywords = ["매출액", "영업이익", "당기순이익", "자본총계", "자산총계"]
    df_filtered = df[
        df["account_nm"].apply(lambda x: any(k in x for k in keywords))
    ]

    result = {"2022": {}, "2023": {}, "2024": {}}

    for _, row in df_filtered.iterrows():
        account = normalize(row["account_nm"])
        result["2022"][account] = clean(row.get("bfefrmtrm_amount"))
        result["2023"][account] = clean(row.get("frmtrm_amount"))
        result["2024"][account] = clean(row.get("thstrm_amount"))


    for year in ["2022", "2023", "2024"]:
        result[year]["ratio"] = calculate_ratios(result[year])

    return result