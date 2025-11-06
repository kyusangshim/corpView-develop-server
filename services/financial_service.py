import json
import asyncio
import pandas as pd
import redis.asyncio as redis
from sqlalchemy.orm import Session
from repository import financials_repository
from clients import dart_api_client
from utils.utils import clean, normalize, calculate_ratios, _format_financials_from_orm

FINANCIALS_TTL = 86400  # 24시간

class FinancialService:
    def __init__(self, redis_client: redis.Redis, SessionLocal):
        self.redis = redis_client
        self.SessionLocal = SessionLocal

    async def get_financials(self, corp_code: str):
        """(Worker) 재무 정보의 L1 -> L2 -> L3 캐싱 로직을 담당"""
        key = f"details:financials:{corp_code}"

        # Redis 먼저 확인
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        db = self.SessionLocal()

        try:
            # 2. (L2) RDB 조회
            l2_data = await asyncio.to_thread(
                financials_repository.get_financials_by_code, db, corp_code
            )
            if l2_data:
                raw_data = _format_financials_from_orm(l2_data)
                await self.redis.set(key, json.dumps(raw_data), ex=FINANCIALS_TTL)
                return raw_data

            # 3. (L3) DART API 호출
            raw = await dart_api_client.fetch_financial_raw(corp_code)

            df = pd.DataFrame(raw["list"])
            if "fs_div" not in df.columns:
                return {"message": "'fs_div' 정보가 없습니다."}

            df = df[df["fs_div"].isin(["CFS", "OFS"])]
            if df.empty:
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

            # L2 저장
            await asyncio.to_thread(financials_repository.upsert_financials, db, corp_code, result)
            await asyncio.to_thread(db.commit)

            await self.redis.set(key, json.dumps(result), ex=FINANCIALS_TTL)
            return result

        except Exception as e:
            await asyncio.to_thread(db.rollback)
            raise e
        finally:
            await asyncio.to_thread(db.close)
