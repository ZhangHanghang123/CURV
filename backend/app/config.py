"""应用配置管理"""
import os
from pydantic_settings import BaseSettings

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    """应用配置"""
    PROJECT_NAME: str = "CURV"
    # 数据库
    DATABASE_URL: str = "mysql+pymysql://curv:Curv%402026@127.0.0.1:3306/curv_db?charset=utf8mb4"
    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    # JWT
    SECRET_KEY: str = "curv-dev-secret-key-change-in-production-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # 服务
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8003
    DEBUG: bool = True
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5174", "http://127.0.0.1:5174"]
    # 数据目录
    DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"


settings = Settings()
os.makedirs(settings.DATA_DIR, exist_ok=True)