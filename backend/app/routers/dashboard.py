"""总览看板 API"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..schemas import ResponseBase
from ..dependencies import get_current_user
from ..models import (
    CurvCurveDefinition, CurvRateData, CurvDataSource,
    CurvCollectionLog, CurvScenario, CurvScenarioResult,
)

router = APIRouter(prefix="/api/dashboard", tags=["总览看板"])


@router.get("", response_model=ResponseBase)
def overview(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """总览看板数据"""
    # 1. 曲线总数
    curve_count = db.query(func.count(CurvCurveDefinition.id)).filter(
        CurvCurveDefinition.status == 1, CurvCurveDefinition.is_deleted == 0,
    ).scalar() or 0

    # 2. 数据源
    source_count = db.query(func.count(CurvDataSource.id)).filter(
        CurvDataSource.status == 1, CurvDataSource.is_deleted == 0,
    ).scalar() or 0

    # 3. 今日采集成功率
    today = date.today()
    today_logs = db.query(CurvCollectionLog).filter(
        func.date(CurvCollectionLog.start_time) == today,
    ).all()
    total_runs = len(today_logs)
    success_runs = sum(1 for r in today_logs if r.status == "success")
    success_rate = round(success_runs / total_runs * 100, 1) if total_runs > 0 else 100.0

    # 4. 在管期限点（最新一日）
    latest_date = db.query(func.max(CurvRateData.trade_date)).scalar()
    tenor_count = db.query(func.count(CurvRateData.id)).filter(
        CurvRateData.trade_date == latest_date,
        CurvRateData.source_version == "official",
        CurvRateData.data_status == "active",
    ).scalar() or 0

    # 5. 情景数
    scenario_count = db.query(func.count(CurvScenario.id)).filter(
        CurvScenario.status == 1, CurvScenario.is_deleted == 0,
    ).scalar() or 0

    # 6. 最新一天的 10Y 国债利率
    row = (
        db.query(CurvRateData)
        .filter(
            CurvRateData.curve_code == "cnb_treasury_yield",
            CurvRateData.tenor == "10Y",
            CurvRateData.source_version == "official",
        )
        .order_by(CurvRateData.trade_date.desc())
        .first()
    )
    rate_10y = float(row.rate_value) if row else None
    rate_10y_date = row.trade_date.isoformat() if row else None

    # 7. 10Y-1Y 利差（基于 10Y 和 1Y 国债）
    rows = (
        db.query(CurvRateData)
        .filter(
            CurvRateData.curve_code == "cnb_treasury_yield",
            CurvRateData.tenor.in_(["10Y", "1Y"]),
            CurvRateData.source_version == "official",
        )
        .order_by(CurvRateData.trade_date.desc())
        .limit(2)
        .all()
    )
    rate_dict = {r.tenor: float(r.rate_value) for r in rows}
    spread_10y_1y_bp = round((rate_dict.get("10Y", 0) - rate_dict.get("1Y", 0)) * 100, 1) if "10Y" in rate_dict and "1Y" in rate_dict else None

    # 8. 最新采集状态
    latest_logs = (
        db.query(CurvCollectionLog)
        .order_by(CurvCollectionLog.start_time.desc())
        .limit(5)
        .all()
    )
    recent_logs = [
        {
            "task_id": r.task_id, "start_time": r.start_time.isoformat(),
            "status": r.status, "record_count": r.record_count, "duration_ms": r.duration_ms,
        }
        for r in latest_logs
    ]

    return ResponseBase(data={
        "kpi": {
            "curve_count": curve_count,
            "source_count": source_count,
            "tenor_count": tenor_count,
            "scenario_count": scenario_count,
            "success_rate": success_rate,
            "rate_10y": rate_10y,
            "rate_10y_date": rate_10y_date,
            "spread_10y_1y_bp": spread_10y_1y_bp,
        },
        "latest_date": latest_date.isoformat() if latest_date else None,
        "recent_logs": recent_logs,
    })