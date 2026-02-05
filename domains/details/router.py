from fastapi import APIRouter, Query, Depends

from domains.details.schema import CompanyDetailResponse
from core.deps import get_details_usecase
from domains.details.usecase import DetailsUseCase

router = APIRouter()

@router.get("/company-details", response_model=CompanyDetailResponse)
async def get_integrated_company_details_final(
    name: str = Query(...),
    usecase: DetailsUseCase = Depends(get_details_usecase),
):
    return await usecase.get_company_details(name)
