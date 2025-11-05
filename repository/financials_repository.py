# /repository/financials_repository.py

from sqlalchemy.orm import Session
from models.financial_statement import FinancialStatement
from typing import Dict, Any, List

def get_financials_by_code(db: Session, corp_code: str) -> List[FinancialStatement]:
    """L2(RDB)에서 특정 회사의 모든 재무제표를 조회합니다."""
    return (
        db.query(FinancialStatement)
        .filter(FinancialStatement.corp_code == corp_code)
        .order_by(FinancialStatement.year.asc())
        .all()
    )

def upsert_financials(db: Session, corp_code: str, financial_data: Dict[str, Any]):
    """
    L3(DART)에서 가져온 데이터를 L2(RDB)에 Upsert(Update or Insert)합니다.
    """
    for year, data in financial_data.items():
        if not (isinstance(data, dict) and "매출액" in data):
            continue # 유효하지 않은 데이터(예: "message: ...") 스킵
        
        # 1. (Upsert) 기존 데이터가 있는지 확인
        existing = (
            db.query(FinancialStatement)
            .filter_by(corp_code=corp_code, year=int(year))
            .first()
        )
        
        if existing:
            # 2. (Update)
            existing.revenue = data.get("매출액")
            existing.operating_profit = data.get("영업이익")
            existing.net_income = data.get("당기순이익")
            existing.total_assets = data.get("자산총계")
            existing.total_equity = data.get("자본총계") # 스키마에 따라 추가
            existing.ratios = data.get("ratio")
        else:
            # 3. (Insert)
            new_statement = FinancialStatement(
                corp_code=corp_code,
                year=int(year),
                revenue=data.get("매출액"),
                operating_profit=data.get("영업이익"),
                net_income=data.get("당기순이익"),
                total_assets=data.get("자산총계"),
                total_equity=data.get("자본총계"),
                ratios=data.get("ratio"),
            )
            db.add(new_statement)
    
    # 4. 트랜잭션은 Service 계층에서 commit/rollback 관리 (여기서는 안 함)