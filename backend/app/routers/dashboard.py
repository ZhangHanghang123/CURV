"""总览看板 API"""
from datetime import date, timedelta, datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..schemas import ResponseBase
from ..dependencies import get_current_user
from ..models import (
    CurvCurveDefinition, CurvRateData, CurvDataSource,
    CurvCollectionLog, CurvScenario, CurvScenarioResult,
    CurvDerivedCurve, CurvFittingParam, CurvShapeMetric,
    CurvBacktestResult, CurvSmartDialogue, CurvCurvePoint,
)

router = APIRouter(prefix="/api/dashboard", tags=["总览看板"])


# 曲线类型 → 中文标签 / 颜色
CURVE_CATEGORY_LABEL = {
    "base": "基准曲线",
    "credit": "信用曲线",
    "swap": "互换曲线",
    "derived": "衍生曲线",
    "ftp": "FTP曲线",
}
CURVE_CATEGORY_COLOR = {
    "base": "#1677ff",
    "credit": "#722ed1",
    "swap": "#52c41a",
    "derived": "#fa8c16",
    "ftp": "#13c2c2",
}
# 数据源类型 → 中文 / 颜色
SOURCE_TYPE_LABEL = {
    "official": "官方",
    "api": "接口",
    "broker": "经纪商",
    "internal": "内部",
    "manual": "手工",
}
SOURCE_TYPE_COLOR = {
    "official": "#1677ff",
    "api": "#52c41a",
    "broker": "#fa8c16",
    "internal": "#722ed1",
    "manual": "#8c8c8c",
}


@router.get("", response_model=ResponseBase)
def overview(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """总览看板数据 - 类ALMD/IALMD风格丰富版"""
    today = date.today()

    # ────────── KPI 第一行：核心资产 ──────────
    curve_count = db.query(func.count(CurvCurveDefinition.id)).filter(
        CurvCurveDefinition.status == 1, CurvCurveDefinition.is_deleted == 0,
    ).scalar() or 0

    source_count = db.query(func.count(CurvDataSource.id)).filter(
        CurvDataSource.status == 1, CurvDataSource.is_deleted == 0,
    ).scalar() or 0

    latest_date = db.query(func.max(CurvRateData.trade_date)).scalar()
    tenor_count = db.query(func.count(CurvRateData.id)).filter(
        CurvRateData.trade_date == latest_date,
        CurvRateData.source_version == "official",
        CurvRateData.data_status == "active",
    ).scalar() or 0 if latest_date else 0

    rate_total = db.query(func.count(CurvRateData.id)).filter(
        CurvRateData.source_version == "official",
    ).scalar() or 0

    today_logs = db.query(CurvCollectionLog).filter(
        func.date(CurvCollectionLog.start_time) == today,
    ).all()
    total_runs = len(today_logs)
    success_runs = sum(1 for r in today_logs if r.status == "success")
    success_rate = round(success_runs / total_runs * 100, 1) if total_runs > 0 else 100.0

    # ────────── KPI 第二行：能力 ──────────
    derived_count = db.query(func.count(CurvDerivedCurve.id)).filter(
        CurvDerivedCurve.is_enabled == 1, CurvDerivedCurve.is_deleted == 0,
    ).scalar() or 0

    scenario_count = db.query(func.count(CurvScenario.id)).filter(
        CurvScenario.is_enabled == 1, CurvScenario.is_deleted == 0,
    ).scalar() or 0

    fit_count = db.query(func.count(CurvFittingParam.id)).scalar() or 0
    shape_count = db.query(func.count(CurvShapeMetric.id)).scalar() or 0

    backtest_count = db.query(func.count(CurvBacktestResult.id)).scalar() or 0

    session_count = db.query(func.count(func.distinct(CurvSmartDialogue.session_id))).scalar() or 0
    message_count = db.query(func.count(CurvSmartDialogue.id)).scalar() or 0

    # ────────── 趋势：10Y国债最近30天 ──────────
    trend_10y = []
    if latest_date:
        start_d = latest_date - timedelta(days=29)
        rows = (
            db.query(CurvRateData.trade_date, CurvRateData.rate_value)
            .filter(
                CurvRateData.curve_code == "cnb_treasury_yield",
                CurvRateData.tenor == "10Y",
                CurvRateData.source_version == "official",
                CurvRateData.trade_date >= start_d,
            )
            .order_by(CurvRateData.trade_date)
            .all()
        )
        trend_10y = [
            {"period": r.trade_date.strftime("%m-%d"), "value": round(float(r.rate_value), 4)}
            for r in rows
        ]

    # ────────── 趋势：10Y-1Y 利差最近30天 ──────────
    spread_trend = []
    if latest_date:
        start_d = latest_date - timedelta(days=29)
        rows = (
            db.query(CurvRateData.trade_date, CurvRateData.tenor, CurvRateData.rate_value)
            .filter(
                CurvRateData.curve_code == "cnb_treasury_yield",
                CurvRateData.tenor.in_(["10Y", "1Y"]),
                CurvRateData.source_version == "official",
                CurvRateData.trade_date >= start_d,
            )
            .order_by(CurvRateData.trade_date)
            .all()
        )
        # 拼成 {date: {tenor: rate}}
        by_date: dict = {}
        for r in rows:
            d = r.trade_date.strftime("%m-%d")
            by_date.setdefault(d, {})[r.tenor] = float(r.rate_value)
        for d in sorted(by_date.keys()):
            v = by_date[d]
            if "10Y" in v and "1Y" in v:
                spread_trend.append({
                    "period": d,
                    "value": round((v["10Y"] - v["1Y"]) * 100, 1),  # bp
                })

    # ────────── 多曲线快照（最新一天的关键期限） ──────────
    snapshot_curves = []
    if latest_date:
        # 动态取数据量最大的 3 条曲线（最新一天）
        top_curve_rows = (
            db.query(
                CurvRateData.curve_code,
                func.count(CurvRateData.id).label("cnt"),
            )
            .filter(
                CurvRateData.trade_date == latest_date,
                CurvRateData.source_version == "official",
                CurvRateData.data_status == "active",
            )
            .group_by(CurvRateData.curve_code)
            .order_by(func.count(CurvRateData.id).desc())
            .limit(3)
            .all()
        )
        top_curve_codes = [r.curve_code for r in top_curve_rows]
        rows = (
            db.query(CurvRateData.curve_code, CurvRateData.tenor, CurvRateData.rate_value)
            .filter(
                CurvRateData.curve_code.in_(top_curve_codes),
                CurvRateData.tenor.in_(["1Y", "3Y", "5Y", "10Y"]),
                CurvRateData.source_version == "official",
                CurvRateData.trade_date == latest_date,
            )
            .all()
        )
        snap: dict = {}
        for r in rows:
            snap.setdefault(r.curve_code, {})[r.tenor] = round(float(r.rate_value), 4)
        name_rows = (
            db.query(CurvCurveDefinition.code, CurvCurveDefinition.name)
            .filter(CurvCurveDefinition.code.in_(top_curve_codes))
            .all()
        )
        curve_name_map = {r.code: r.name for r in name_rows}
        for code in top_curve_codes:
            if code in snap and snap[code]:
                name = curve_name_map.get(code, code)
                short_name = name.replace("中债", "").replace("收益率", "").replace("(合成)", "").strip()
                snapshot_curves.append({"name": short_name or code, "code": code, "rates": snap[code]})

    # ────────── 曲线分类分布 ──────────
    category_rows = (
        db.query(CurvCurveDefinition.curve_category, func.count(CurvCurveDefinition.id))
        .filter(CurvCurveDefinition.is_deleted == 0, CurvCurveDefinition.status == 1)
        .group_by(CurvCurveDefinition.curve_category)
        .all()
    )
    curve_category_dist = [
        {
            "label": CURVE_CATEGORY_LABEL.get(cat, cat or "未分类"),
            "key": cat or "unknown",
            "count": cnt,
            "color": CURVE_CATEGORY_COLOR.get(cat, "#8c8c8c"),
        }
        for cat, cnt in category_rows
    ]

    # ────────── 数据源类型分布 ──────────
    source_rows = (
        db.query(CurvDataSource.source_type, func.count(CurvDataSource.id))
        .filter(CurvDataSource.is_deleted == 0, CurvDataSource.status == 1)
        .group_by(CurvDataSource.source_type)
        .all()
    )
    source_type_dist = [
        {
            "label": SOURCE_TYPE_LABEL.get(t, t or "其他"),
            "key": t or "unknown",
            "count": cnt,
            "color": SOURCE_TYPE_COLOR.get(t, "#8c8c8c"),
        }
        for t, cnt in source_rows
    ]

    # ────────── 期限分布（最新一天各期限点的曲线数） ──────────
    tenor_dist = []
    if latest_date:
        rows = (
            db.query(CurvRateData.tenor, func.count(func.distinct(CurvRateData.curve_code)))
            .filter(
                CurvRateData.trade_date == latest_date,
                CurvRateData.source_version == "official",
                CurvRateData.data_status == "active",
            )
            .group_by(CurvRateData.tenor)
            .all()
        )
        for t, cnt in rows:
            tenor_dist.append({"label": t, "count": cnt, "color": "#722ed1"})

    # ────────── 利率排行：10Y最高 / 最低 ──────────
    top_rates = []
    if latest_date:
        rows = (
            db.query(
                CurvCurveDefinition.code, CurvCurveDefinition.name,
                CurvRateData.rate_value,
            )
            .join(CurvRateData, CurvRateData.curve_code == CurvCurveDefinition.code)
            .filter(
                CurvRateData.trade_date == latest_date,
                CurvRateData.tenor == "10Y",
                CurvRateData.source_version == "official",
                CurvRateData.data_status == "active",
                CurvCurveDefinition.is_deleted == 0,
            )
            .order_by(CurvRateData.rate_value.desc())
            .limit(8)
            .all()
        )
        for i, r in enumerate(rows, 1):
            top_rates.append({
                "rank": i,
                "curve_code": r.code,
                "curve_name": r.name,
                "value": round(float(r.rate_value), 4),
            })

    # ────────── 采集状态汇总 ──────────
    last7_logs = (
        db.query(CurvCollectionLog)
        .filter(CurvCollectionLog.start_time >= datetime.now() - timedelta(days=7))
        .all()
    )
    status_dist = {"success": 0, "failed": 0, "running": 0}
    for l in last7_logs:
        if l.status == "success":
            status_dist["success"] += 1
        elif l.status == "failed":
            status_dist["failed"] += 1
        else:
            status_dist["running"] += 1

    # ────────── 最近采集日志 ──────────
    recent_logs = []
    latest_logs = (
        db.query(CurvCollectionLog)
        .order_by(CurvCollectionLog.start_time.desc())
        .limit(8)
        .all()
    )
    for r in latest_logs:
        recent_logs.append({
            "task_id": r.task_id,
            "source_id": r.source_id,
            "trade_date": r.trade_date.isoformat() if r.trade_date else "",
            "start_time": r.start_time.isoformat() if r.start_time else "",
            "status": r.status,
            "record_count": r.record_count,
            "duration_ms": r.duration_ms,
            "error_msg": (r.error_msg or "")[:60],
        })

    # ────────── 关键利率点（最新一天） ──────────
    key_rate_points = []
    if latest_date:
        rows = (
            db.query(CurvRateData.tenor, CurvRateData.rate_value)
            .filter(
                CurvRateData.curve_code == "cnb_treasury_yield",
                CurvRateData.tenor.in_(["3M", "1Y", "5Y", "10Y", "30Y"]),
                CurvRateData.source_version == "official",
                CurvRateData.trade_date == latest_date,
            )
            .all()
        )
        for r in rows:
            key_rate_points.append({"tenor": r.tenor, "value": round(float(r.rate_value), 4)})

    return ResponseBase(data={
        "kpi": {
            # 第一行
            "curve_count": curve_count,
            "source_count": source_count,
            "tenor_count": tenor_count,
            "rate_total": rate_total,
            "success_rate": success_rate,
            "latest_date": latest_date.isoformat() if latest_date else None,
            # 第二行
            "derived_count": derived_count,
            "scenario_count": scenario_count,
            "fit_count": fit_count,
            "shape_count": shape_count,
            "backtest_count": backtest_count,
            "session_count": session_count,
            "message_count": message_count,
            # 关键
            "rate_10y": round(float(key_rate_points[2]["value"]), 4) if len(key_rate_points) >= 3 else None,
        },
        # 趋势
        "trend_10y": trend_10y,
        "spread_trend": spread_trend,
        # 多曲线对比
        "snapshot_curves": snapshot_curves,
        # 分布
        "curve_category_dist": curve_category_dist,
        "source_type_dist": source_type_dist,
        "tenor_dist": tenor_dist,
        # 排行
        "top_rates": top_rates,
        # 状态
        "status_dist": status_dist,
        # 日志
        "recent_logs": recent_logs,
        # 关键利率
        "key_rate_points": key_rate_points,
        # 兼容旧字段
        "rate_10y_date": latest_date.isoformat() if latest_date else None,
        "spread_10y_1y_bp": spread_trend[-1]["value"] if spread_trend else None,
    })
