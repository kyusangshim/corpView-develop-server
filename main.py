from core.config import SECRET_KEY
from fastapi import FastAPI, Request, Response

from domains.details.router import router as details_router
from domains.companies.router import router as companies_router
from domains.industries.router import router as industries_router
from domains.auth.router import router as auth_router
from domains.users.router import router as user_router

from core.db.database import Base, engine
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:3000/",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3000/",
]
# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


Base.metadata.create_all(bind=engine)


app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(companies_router, prefix="/companies", tags=["Companies"])
app.include_router(industries_router, prefix="/industries", tags=["Industries"])
app.include_router(details_router, prefix="/details-final", tags=["Company Details (Final)"])