# /services/auth_service.py

from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import jwt, uuid
from starlette.responses import RedirectResponse

from core.database import get_db
from core.config import SECRET_KEY, FRONTEND_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from domains.users import repository as user_repository
from models.user import User
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/callback/google")


def create_access_token(data: dict, expires_seconds: int = 3600) -> str:
    """JWT 토큰을 생성합니다."""
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

async def handle_google_callback(request: Request, db: Session) -> RedirectResponse:
    """Google 로그인 콜백을 처리하고 JWT를 발급한 뒤 리디렉션합니다."""
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info or "email" not in user_info:
        raise HTTPException(status_code=400, detail="구글 사용자 정보 조회 실패")

    user = user_repository.get_user_by_oauth(
        db, provider="google", sub=user_info["sub"]
    )
    
    if not user:
        user = user_repository.create_user_from_oauth(db, user_info)

    access_token = create_access_token({"user_id": user.id})
    redirect_to = f"{FRONTEND_URL}/dashboard?token={access_token}"
    return RedirectResponse(redirect_to)

async def get_current_user(
    token: str = Security(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """JWT 토큰을 검증하고 현재 사용자를 반환합니다."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다")

    user = user_repository.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user