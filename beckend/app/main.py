from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import webhook, session, auth, test_trading

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
app.include_router(session.router, prefix=settings.api_prefix, tags=["session"])
app.include_router(auth.router, prefix=settings.api_prefix, tags=["auth"])
app.include_router(test_trading.router, prefix=settings.api_prefix, tags=["test"])

@app.on_event("startup")
async def startup_event():
    # SQLite 데이터베이스는 자동으로 초기화됩니다
    print("성공007: Next Auto Trading System 시작됨")
    print("성공007: FastAPI 서버가 정상적으로 시작되었습니다.")
    print("성공007: 포트 8000에서 서비스 중...")
    print("성공007: 계좌 잔고 조회 API 추가 완료")

@app.on_event("shutdown")
async def shutdown_event():
    # SQLite 연결은 자동으로 관리됩니다
    pass