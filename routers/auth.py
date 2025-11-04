# /routers/auth.py

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.token import Token
from schemas.user import UserOut
from models.user import User
from services.auth_service import (
    oauth, 
    handle_google_callback, 
    get_current_user
)

router = APIRouter(tags=["Auth"])

@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth_callback_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google", name="auth_callback_google", response_model=Token)
async def auth_callback_google(request: Request, db: Session = Depends(get_db)):
    return await handle_google_callback(request, db)


@router.get("/me", response_model=UserOut)
async def read_current_user(
    current_user: User = Depends(get_current_user) # service에서 임포트
):
    return current_user