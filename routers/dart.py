from fastapi import Depends, APIRouter
from services import dart_api_service


router = APIRouter()

@router.get("/financials")
async def get_financials(code: str):
    """(외부 API) DART API로 재무 정보를 조회하고 가공합니다."""
    # 모든 복잡한 로직은 서비스 계층에 위임
    return await dart_api_service.fetch_and_process_financials(code)
