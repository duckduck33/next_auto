from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # BingX API 설정 (기본값으로 설정, 프론트엔드에서 동적으로 설정됨)
    bingx_api_key: str = ""
    bingx_secret_key: str = ""
    bingx_url: str = "https://open-api-vst.bingx.com"

    # MongoDB 설정
    mongo_uri: str = "mongodb://localhost:27017"
    database_name: str = "tv_auto"

    # FastAPI 설정
    app_name: str = "TradingView Auto Trading"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()