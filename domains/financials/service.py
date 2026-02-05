# domains/financials/service.py

import json
import asyncio
import pandas as pd
import redis.asyncio as redis
from sqlalchemy.orm import Session

from clients import dart_api_client
from utils.utils import clean, normalize, calculate_ratios, _format_financials_from_orm
from core.Redis.keys import details_financials_key
from core.db.db_background import fire_and_forget_db

from domains.financials import repository as financials_repository

FINANCIALS_TTL = 86400  # 24시간


class FinancialService:
    def __init__(self, redis_client: redis.Redis, SessionLocal):
        self.redis = redis_client
        self.SessionLocal = SessionLocal

    async def get_financials(self, corp_code: str):
        key = details_financials_key(corp_code)

        # L1
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        # L2
        db: Session = self.SessionLocal()
        try:
            l2_data = await asyncio.to_thread(
                financials_repository.get_financials_by_code, db, corp_code
            )
            if l2_data:
                raw_data = _format_financials_from_orm(l2_data)
                await self.redis.set(key, json.dumps(raw_data), ex=FINANCIALS_TTL)
                return raw_data
        finally:
            await asyncio.to_thread(db.close)

        # L3 (DART)
        raw = await dart_api_client.fetch_financial_raw(corp_code)

        df = pd.DataFrame(raw["list"])
        if "fs_div" not in df.columns:
            return {"message": "'fs_div' 정보가 없습니다."}

        if (df["fs_div"] == "CFS").any():
            df = df[df["fs_div"] == "CFS"]
        elif (df["fs_div"] == "OFS").any():
            df = df[df["fs_div"] == "OFS"]
        else:
            return {"message": "CFS/OFS 기준 데이터가 없습니다."}

        keywords = ["매출액", "영업이익", "당기순이익", "자본총계", "자산총계"]
        df_filtered = df[df["account_nm"].apply(lambda x: any(k in x for k in keywords))]

        result = {"2022": {}, "2023": {}, "2024": {}}
        for _, row in df_filtered.iterrows():
            account = normalize(row["account_nm"])
            result["2022"][account] = clean(row.get("bfefrmtrm_amount"))
            result["2023"][account] = clean(row.get("frmtrm_amount"))
            result["2024"][account] = clean(row.get("thstrm_amount"))

        for year in result:
            result[year]["ratio"] = calculate_ratios(result[year])

        # L1 저장
        await self.redis.set(key, json.dumps(result), ex=FINANCIALS_TTL)

        # L2 저장 (Fire-and-Forget)
        fire_and_forget_db(
            self.SessionLocal,
            financials_repository.upsert_financials,
            corp_code,
            result,
        )

        return result
