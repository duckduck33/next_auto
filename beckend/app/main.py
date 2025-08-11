from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api import webhook, profit, session, calendar

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 origin을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 라우트
@app.get("/")
async def root():
    return {
        "message": "Welcome to TradingView Auto Trading API",
        "version": settings.app_version,
    }

# API 라우터 등록
app.include_router(webhook.router, prefix=settings.api_prefix, tags=["webhook"])
app.include_router(profit.router, prefix=settings.api_prefix, tags=["profit"])
app.include_router(session.router, prefix=settings.api_prefix, tags=["session"])
app.include_router(calendar.router, prefix=settings.api_prefix, tags=["calendar"])

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()