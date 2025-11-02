# /routers/auth.py
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request, HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import jwt, uuid, os
from core.database import get_db
from models.user import User
from schemas.token import Token
from schemas.user import UserOut
from starlette.responses import RedirectResponse
from core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, FRONTEND_URL



router = APIRouter(tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/callback/google")

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)  # 구글 OAuth2 클라이언트 등록 :contentReference[oaicite:1]{index=1}


@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth_callback_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


def create_access_token(data: dict, expires_seconds: int = 3600):
    now = datetime.now(timezone.utc)
    to_encode = data.copy()
    to_encode.update(
        {
            "iat": now,
            "jti": str(uuid.uuid4()),
            "exp": now + timedelta(seconds=expires_seconds),
        }
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")


@router.get("/callback/google", name="auth_callback_google", response_model=Token)
async def auth_callback_google(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info or "email" not in user_info:
        raise HTTPException(status_code=400, detail="구글 사용자 정보 조회 실패")
    # 1) DB에서 사용자 조회 또는 신규 생성
    user = (
        db.query(User)
        .filter_by(oauth_provider="google", oauth_sub=user_info["sub"])
        .first()
    )
    if not user:
        user = User(
            email=user_info["email"],
            name=user_info.get("name"),
            oauth_provider="google",
            oauth_sub=user_info["sub"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    # 2) JWT 발급
    access_token = create_access_token({"user_id": user.id})
    redirect_to = f"{FRONTEND_URL}/dashboard?token={access_token}"
    return RedirectResponse(redirect_to)


async def get_current_user(
    token: str = Security(oauth2_scheme), db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
