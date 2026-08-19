"""CURV 收益率曲线平台 — FastAPI 主入口"""
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .cache import redis_client
from .database import SessionLocal
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

# ============== 定时调度：每日 18:30 自动增量采集 ==============
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def scheduled_daily_collect():
    """工作日 18:30 增量采集所有曲线"""
    from .services.collector import CollectorService
    db = SessionLocal()
    try:
        svc = CollectorService(db)
        result = svc.collect_increment(
            source_code="auto_collector_inc",
            operator="scheduler",
        )
        print(f"[{datetime.now().isoformat()}] 定时增量采集完成: {result['total_records']} 条, "
              f"耗时 {result['duration_ms']}ms")
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] 定时增量采集失败: {e}")
    finally:
        db.close()


@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(
        scheduled_daily_collect,
        CronTrigger(day_of_week="mon-fri", hour=18, minute=30),
        id="curv_daily_collect",
        name="CURV 每日增量采集",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    print(f"[{datetime.now().isoformat()}] 定时调度已启动：CURV 工作日 18:30 增量采集")


@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown(wait=False)


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