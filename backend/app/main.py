"""CURV 收益率曲线平台 — FastAPI 主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .cache import redis_client
from .routers import auth, dashboard, curves, rates, build, analysis, scenario, service, agent, dict, collection


app = FastAPI(
    title="CURV 收益率曲线管理与建模分析平台",
    description="AI驱动的收益率曲线数据底座 + 构建引擎 + 智能分析平台",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(dict.router)
app.include_router(curves.router)
app.include_router(rates.router)
app.include_router(build.router)
app.include_router(analysis.router)
app.include_router(scenario.router)
app.include_router(service.router)
app.include_router(agent.router)
app.include_router(collection.router)


@app.get("/")
def root():
    return {
        "name": "CURV API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "description": "收益率曲线管理与建模分析平台",
    }


@app.get("/api/health")
def health_check():
    redis_ok = False
    try:
        redis_client.ping()
        redis_ok = True
    except Exception:
        pass

    mysql_ok = False
    try:
        from sqlalchemy import text
        from .database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            mysql_ok = True
    except Exception:
        pass

    return {
        "status": "ok",
        "mysql": "connected" if mysql_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
    }