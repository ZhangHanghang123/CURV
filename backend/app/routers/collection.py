"""数据采集 API（按业务规则采集历史数据）"""
import time
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CurvCollectionLog, CurvCollectionTask, CurvDataSource
from ..schemas import ResponseBase
from ..dependencies import get_current_user
from ..services.collector import CollectorService, COLLECTION_RULES

router = APIRouter(prefix="/api/collection", tags=["数据采集"])


@router.get("/rules", response_model=ResponseBase)
def list_rules(user: dict = Depends(get_current_user)):
    """列出所有曲线的业务采集规则"""
    rules = []
    for code, rule in COLLECTION_RULES.items():
        rules.append({
            "curve_code": code,
            "frequency": rule["frequency"],
            "category": rule["category"],
            "current_value": rule.get("current_value"),
            "volatility_bp": rule.get("volatility_bp"),
            "year_trend_bp": rule.get("year_trend_bp"),
            "derived_from": rule.get("derived_from"),
        })
    return ResponseBase(data=rules)


@router.post("/run", response_model=ResponseBase)
def collect_history(
    payload: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """触发历史数据采集
    payload: {
        "start_date": "2025-08-18",  # 1 年前
        "end_date": "2026-08-17",     # 今天
        "curve_codes": [...] (可选, 默认全部),
        "source_code": "auto_collector" (可选)
    }
    """
    start_str = payload.get("start_date")
    end_str = payload.get("end_date")
    curve_codes = payload.get("curve_codes")  # None = 全部
    source_code = payload.get("source_code", "auto_collector")

    if not start_str or not end_str:
        raise HTTPException(status_code=400, detail="start_date 和 end_date 必填")

    start_date = date.fromisoformat(start_str)
    end_date = date.fromisoformat(end_str)

    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date 不能早于 start_date")

    days_diff = (end_date - start_date).days
    if days_diff > 730:  # 最多 2 年
        raise HTTPException(status_code=400, detail="采集范围不能超过 2 年")

    svc = CollectorService(db)
    try:
        result = svc.collect_history(
            start_date=start_date,
            end_date=end_date,
            curve_codes=curve_codes,
            source_code=source_code,
            operator=str(user.get("id", "system")),
        )
        return ResponseBase(
            data=result,
            message=f"采集完成：{result['total_records']} 条记录，耗时 {result['duration_ms']}ms",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"采集失败：{str(e)}")


@router.post("/run-increment", response_model=ResponseBase)
def run_increment(
    payload: dict = {},
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """增量采集：每条曲线只采集最后 trade_date+1 ~ today
    payload: {"curve_codes": [...] (可选)}
    """
    curve_codes = payload.get("curve_codes")
    source_code = payload.get("source_code", "auto_collector_inc")
    try:
        svc = CollectorService(db)
        result = svc.collect_increment(
            curve_codes=curve_codes,
            source_code=source_code,
            operator=str(user.get("username", "user")),
        )
        return ResponseBase(
            data=result,
            message=f"增量采集完成：{result['total_records']} 条记录，耗时 {result['duration_ms']}ms",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"增量采集失败：{str(e)}")


@router.get("/logs", response_model=ResponseBase)
def list_logs(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """采集执行日志"""
    rows = (
        db.query(CurvCollectionLog)
        .order_by(CurvCollectionLog.start_time.desc())
        .limit(limit)
        .all()
    )
    return ResponseBase(data=[
        {
            "id": r.id,
            "task_id": r.task_id,
            "source_id": r.source_id,
            "trade_date": r.trade_date.isoformat() if r.trade_date else None,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "duration_ms": r.duration_ms,
            "status": r.status,
            "record_count": r.record_count,
            "error_code": r.error_code,
            "error_msg": (r.error_msg or "")[:200],
        }
        for r in rows
    ])


@router.get("/tasks", response_model=ResponseBase)
def list_tasks(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """采集任务列表"""
    rows = (
        db.query(CurvCollectionTask)
        .order_by(CurvCollectionTask.created_at.desc())
        .limit(limit)
        .all()
    )
    return ResponseBase(data=[
        {
            "id": r.id,
            "task_code": r.task_code,
            "task_name": r.task_name,
            "schedule_type": r.schedule_type,
            "is_enabled": bool(r.is_enabled),
            "params": r.params_json,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ])


@router.get("/sources", response_model=ResponseBase)
def list_sources(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """数据源列表"""
    rows = (
        db.query(CurvDataSource)
        .filter(CurvDataSource.is_deleted == 0)
        .order_by(CurvDataSource.id)
        .all()
    )
    return ResponseBase(data=[
        {
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "source_type": r.source_type,
            "provider": r.provider,
            "frequency": r.frequency,
            "is_enabled": bool(r.is_enabled),
            "last_run_time": r.last_run_time.isoformat() if r.last_run_time else None,
            "last_run_status": r.last_run_status,
        }
        for r in rows
    ])


@router.get("/stats", response_model=ResponseBase)
def collection_stats(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """采集统计概览"""
    from ..models import CurvRateData
    total_records = db.query(CurvRateData).count()
    sources = db.query(CurvDataSource).filter(CurvDataSource.is_deleted == 0).count()
    tasks = db.query(CurvCollectionTask).count()
    logs = db.query(CurvCollectionLog).count()
    last_log = (
        db.query(CurvCollectionLog)
        .order_by(CurvCollectionLog.start_time.desc())
        .first()
    )

    return ResponseBase(data={
        "total_rate_records": total_records,
        "data_sources": sources,
        "tasks": tasks,
        "execution_logs": logs,
        "last_run": {
            "status": last_log.status if last_log else None,
            "record_count": last_log.record_count if last_log else 0,
            "duration_ms": last_log.duration_ms if last_log else 0,
            "trade_date": last_log.trade_date.isoformat() if last_log and last_log.trade_date else None,
            "start_time": last_log.start_time.isoformat() if last_log and last_log.start_time else None,
        },
    })
