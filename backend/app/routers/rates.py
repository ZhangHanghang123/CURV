"""利率数据查询 API"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CurvRateData, CurvCurveVersion
from ..schemas import ResponseBase
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/rates", tags=["利率数据"])


@router.get("", response_model=ResponseBase)
def query_rates(
    curve_code: str,
    trade_date: Optional[date] = None,
    tenor: Optional[str] = None,
    source_version: str = "official",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 1000,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """查询利率数据"""
    q = db.query(CurvRateData).filter(
        CurvRateData.curve_code == curve_code,
        CurvRateData.source_version == source_version,
        CurvRateData.data_status == "active",
    )
    if trade_date:
        q = q.filter(CurvRateData.trade_date == trade_date)
    if tenor:
        q = q.filter(CurvRateData.tenor == tenor)
    if start_date:
        q = q.filter(CurvRateData.trade_date >= start_date)
    if end_date:
        q = q.filter(CurvRateData.trade_date <= end_date)

    rows = q.order_by(CurvRateData.trade_date.desc(), CurvRateData.tenor).limit(limit).all()
    return ResponseBase(data=[
        {
            "id": r.id, "curve_code": r.curve_code, "trade_date": r.trade_date.isoformat(),
            "tenor": r.tenor, "rate_value": float(r.rate_value), "source_version": r.source_version,
            "data_status": r.data_status, "is_adjusted": r.is_adjusted,
            "data_source_code": r.data_source_code,
        }
        for r in rows
    ])


@router.get("/curve/{curve_code}/{trade_date}", response_model=ResponseBase)
def get_curve_snapshot(
    curve_code: str,
    trade_date: date,
    source_version: str = "official",
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取单日单条曲线的全部期限点（按期限排序）"""
    rows = (
        db.query(CurvRateData)
        .filter(
            CurvRateData.curve_code == curve_code,
            CurvRateData.trade_date == trade_date,
            CurvRateData.source_version == source_version,
            CurvRateData.data_status == "active",
        )
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="未找到曲线数据")

    tenor_to_days = {
        "1D": 1, "7D": 7, "14D": 14, "ON": 1, "1W": 7, "2W": 14,
        "1M": 30, "3M": 90, "6M": 180, "9M": 270, "1Y": 365, "2Y": 730,
        "3Y": 365 * 3, "5Y": 365 * 5, "7Y": 365 * 7,
        "10Y": 365 * 10, "15Y": 365 * 15, "20Y": 365 * 20, "30Y": 365 * 30,
    }
    sorted_rows = sorted(rows, key=lambda x: tenor_to_days.get(str(x.tenor), 0))
    return ResponseBase(data={
        "curve_code": curve_code,
        "trade_date": trade_date.isoformat(),
        "source_version": source_version,
        "tenors": [r.tenor for r in sorted_rows],
        "rates": [float(r.rate_value) for r in sorted_rows],
        "count": len(sorted_rows),
    })


@router.post("/import", response_model=ResponseBase)
def import_rates(
    payload: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """批量导入利率数据

    payload: {"curve_code": "...", "trade_date": "YYYY-MM-DD",
              "source_version": "raw", "rates": [{"tenor": "1Y", "value": 1.77}, ...]}
    """
    curve_code = payload.get("curve_code")
    trade_date_str = payload.get("trade_date")
    source_version = payload.get("source_version", "raw")
    rates = payload.get("rates", [])

    if not curve_code or not trade_date_str or not rates:
        raise HTTPException(status_code=400, detail="参数不完整")

    trade_date = date.fromisoformat(trade_date_str)
    inserted = 0
    for r in rates:
        tenor = r.get("tenor")
        value = r.get("value")
        if not tenor or value is None:
            continue
        # upsert
        existing = (
            db.query(CurvRateData)
            .filter(
                CurvRateData.curve_code == curve_code,
                CurvRateData.trade_date == trade_date,
                CurvRateData.tenor == tenor,
                CurvRateData.source_version == source_version,
            )
            .first()
        )
        if existing:
            existing.rate_value = value
            existing.data_status = "active"
        else:
            db.add(CurvRateData(
                curve_code=curve_code,
                trade_date=trade_date,
                tenor=tenor,
                rate_value=value,
                source_version=source_version,
                data_status="active",
            ))
        inserted += 1
    db.commit()
    return ResponseBase(data={"inserted": inserted, "curve_code": curve_code, "trade_date": trade_date_str})


@router.get("/versions/{curve_code}", response_model=ResponseBase)
def list_versions(
    curve_code: str,
    trade_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """版本管理列表"""
    q = db.query(CurvCurveVersion).filter(CurvCurveVersion.curve_code == curve_code)
    if trade_date:
        q = q.filter(CurvCurveVersion.trade_date == trade_date)
    rows = q.order_by(CurvCurveVersion.trade_date.desc(), CurvCurveVersion.created_at.desc()).limit(100).all()
    return ResponseBase(data=[
        {
            "id": r.id, "curve_code": r.curve_code, "trade_date": r.trade_date.isoformat(),
            "version_no": r.version_no, "version_status": r.version_status,
            "parent_version_no": r.parent_version_no, "operation_type": r.operation_type,
            "operation_reason": r.operation_reason, "operator": r.operator,
            "effective_time": r.effective_time.isoformat() if r.effective_time else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ])


# ========== 利率值按日期维护（曲线点 -> 利率历史） ==========
@router.get("/point-history", response_model=ResponseBase)
def point_history(
    curve_code: str,
    tenor: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """按曲线+期限查询该点的全部日期利率历史"""
    rows = (
        db.query(CurvRateData)
        .filter(
            CurvRateData.curve_code == curve_code,
            CurvRateData.tenor == tenor.upper(),
        )
        .order_by(CurvRateData.trade_date.desc())
        .all()
    )
    return ResponseBase(data=[
        {
            "id": r.id,
            "curve_code": r.curve_code,
            "tenor": r.tenor,
            "trade_date": r.trade_date.isoformat(),
            "rate_value": float(r.rate_value),
            "source_version": r.source_version,
            "data_status": r.data_status,
            "is_adjusted": bool(r.is_adjusted),
            "adjust_reason": r.adjust_reason,
            "remark": r.remark,
            "data_source_code": r.data_source_code,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ])


@router.put("/{rate_id}", response_model=ResponseBase)
def update_rate(
    rate_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """修改单条利率数据"""
    row = db.query(CurvRateData).filter(CurvRateData.id == rate_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="利率记录不存在")
    editable = ("rate_value", "source_version", "data_status", "remark", "is_adjusted", "adjust_reason")
    for f in editable:
        if f in payload:
            setattr(row, f, payload[f])
    if "rate_value" in payload:
        row.adjusted_at = __import__("datetime").datetime.now()
        row.adjusted_by = str(user.get("id", ""))
        row.is_adjusted = 1
    db.commit()
    return ResponseBase(message="利率已更新")


@router.delete("/{rate_id}", response_model=ResponseBase)
def delete_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """删除单条利率数据"""
    row = db.query(CurvRateData).filter(CurvRateData.id == rate_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="利率记录不存在")
    db.delete(row)
    db.commit()
    return ResponseBase(message="已删除")


@router.post("/point-batch", response_model=ResponseBase)
def point_batch(
    payload: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """按曲线+期限批量维护多日期利率
    payload: {
        "curve_code": "...",
        "tenor": "10Y",
        "source_version": "official",
        "records": [
            {"trade_date": "2026-08-15", "rate_value": 2.43},
            {"trade_date": "2026-08-16", "rate_value": 2.44},
            {"trade_date": "2026-08-17", "rate_value": 2.45},
        ]
    }
    """
    curve_code = payload.get("curve_code")
    tenor = payload.get("tenor")
    records = payload.get("records", [])
    source_version = payload.get("source_version", "official")

    if not curve_code or not tenor or not records:
        raise HTTPException(status_code=400, detail="参数不完整")

    inserted, updated = 0, 0
    for rec in records:
        td_str = rec.get("trade_date")
        value = rec.get("rate_value")
        if not td_str or value is None:
            continue
        td = date.fromisoformat(td_str)
        existing = (
            db.query(CurvRateData)
            .filter(
                CurvRateData.curve_code == curve_code,
                CurvRateData.trade_date == td,
                CurvRateData.tenor == tenor,
                CurvRateData.source_version == source_version,
            )
            .first()
        )
        if existing:
            existing.rate_value = value
            updated += 1
        else:
            db.add(CurvRateData(
                curve_code=curve_code,
                trade_date=td,
                tenor=tenor,
                rate_value=value,
                source_version=source_version,
                data_status="active",
            ))
            inserted += 1
    db.commit()
    return ResponseBase(
        data={"inserted": inserted, "updated": updated, "total": inserted + updated},
        message=f"成功插入 {inserted} 条，更新 {updated} 条",
    )