import requests as rq
import pandas as pd
from core.config import DART_API

def fetch_and_process_financials(code: str) -> dict:
    """DART API로 재무 정보를 가져오고 Pandas로 가공합니다."""
    code = "00" + code if len(code) == 6 else code
    url = f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json?crtfc_key={DART_API}&corp_code={code}&bsns_year=2024&reprt_code=11011"
    response = rq.get(url)
    data = response.json()

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

    result = {"2022": {}, "2023": {}, "2024": {}}

    def normalize(name):
        return name.split("(")[0].strip()

    for _, row in df_filtered.iterrows():
        account = normalize(row["account_nm"])
        result["2022"][account] = clean(row.get("bfefrmtrm_amount"))
        result["2023"][account] = clean(row.get("frmtrm_amount"))
        result["2024"][account] = clean(row.get("thstrm_amount"))

    def calculate_ratios(year):
        res = result[year]
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

    for year in ["2022", "2023", "2024"]:
        result[year]["ratio"] = calculate_ratios(year)

    return result