"""曲线定义与数据源管理"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models import (
    CurvCurveDefinition, CurvCurvePoint, CurvDataSource,
    CurvCollectionTask, CurvCollectionLog,
    CurvDerivedCurve, CurvValidationRule, CurvPluginModel,
)
from ..schemas import ResponseBase
from ..dependencies import get_current_user


# ========== 工具：根据 tenor_set 自动同步曲线点 ==========
def _sync_curve_points(db: Session, curve_code: str, tenor_set: List[str],
                       point_unit: str = "percent", point_type: str = "standard",
                       created_by: str = ""):
    """根据 tenor_set 自动同步曲线点：
    - 新增缺失的（rate_value 留空）
    - 删除多余的
    - 保留已存在的（不覆盖用户的 rate_value）
    """
    # 获取当前已有的点
    existing = db.query(CurvCurvePoint).filter(
        CurvCurvePoint.curve_code == curve_code,
        CurvCurvePoint.point_type == "standard",
    ).all()
    existing_tenors = {p.tenor: p for p in existing}
    target_tenors = set(t.upper() for t in tenor_set)

    # 1. 删除多余的
    for tenor, p in existing_tenors.items():
        if tenor not in target_tenors:
            db.delete(p)

    # 2. 新增缺失的（rate_value 留空）
    added = 0
    for idx, tenor in enumerate(tenor_set):
        tenor = tenor.upper()
        if tenor in existing_tenors:
            # 已存在：仅更新 sort_order
            existing_tenors[tenor].sort_order = idx + 1
            continue
        new_p = CurvCurvePoint(
            curve_code=curve_code,
            tenor=tenor,
            rate_value=None,
            point_unit=point_unit,
            point_type=point_type,
            sort_order=idx + 1,
            description="",
            status=1,
            is_deleted=0,
            created_by=created_by,
        )
        db.add(new_p)
        added += 1

    return added

router = APIRouter(prefix="/api/curves", tags=["曲线管理"])


@router.get("/definitions", response_model=ResponseBase)
def list_definitions(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    curve_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """曲线定义列表"""
    q = db.query(CurvCurveDefinition).filter(
        CurvCurveDefinition.status == 1, CurvCurveDefinition.is_deleted == 0,
    )
    if keyword:
        q = q.filter(or_(CurvCurveDefinition.code.contains(keyword), CurvCurveDefinition.name.contains(keyword)))
    if category:
        q = q.filter(CurvCurveDefinition.category == category)
    if curve_type:
        q = q.filter(CurvCurveDefinition.curve_type == curve_type)
    rows = q.order_by(CurvCurveDefinition.id).all()
    return ResponseBase(data=[
        {
            "id": r.id, "code": r.code, "name": r.name,
            "curve_type": r.curve_type, "category": r.category, "currency": r.currency,
            "rate_type_code": r.rate_type_code, "compound_code": r.compound_code,
            "day_count_code": r.day_count_code, "tenor_set": r.tenor_set_json,
            "source_id": r.source_id, "description": r.description, "owner_role": r.owner_role,
            "is_enabled": r.is_enabled, "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ])


@router.get("/definitions/{code}", response_model=ResponseBase)
def get_definition(code: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    row = db.query(CurvCurveDefinition).filter(
        CurvCurveDefinition.code == code, CurvCurveDefinition.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="曲线不存在")
    return ResponseBase(data={
        "id": row.id, "code": row.code, "name": row.name,
        "curve_type": row.curve_type, "curve_category": row.curve_category,
        "category": row.category, "currency": row.currency,
        "rate_type_code": row.rate_type_code, "day_count_method": row.day_count_method,
        "compounding_method": row.compounding_method,
        "interpolation_method": row.interpolation_method,
        "extrapolation_method": row.extrapolation_method,
        "display_unit": row.display_unit, "point_unit": row.point_unit,
        "precision_digits": row.precision_digits, "is_real_time": row.is_real_time,
        "tenor_set": row.tenor_set_json, "source_id": row.source_id, "description": row.description,
    })


@router.post("/definitions", response_model=ResponseBase)
def create_definition(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """新建曲线定义"""
    code = payload.get("code")
    name = payload.get("name")
    if not code or not name:
        raise HTTPException(status_code=400, detail="code 和 name 必填")
    existing = db.query(CurvCurveDefinition).filter(
        CurvCurveDefinition.code == code, CurvCurveDefinition.is_deleted == 0
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"曲线 {code} 已存在")

    row = CurvCurveDefinition(
        code=code,
        name=name,
        curve_type=payload.get("curve_type", "base"),
        curve_category=payload.get("curve_category", "base"),
        category=payload.get("category", "无风险"),
        currency=payload.get("currency", "CNY"),
        rate_type_code=payload.get("rate_type_code", "yield_to_maturity"),
        day_count_method=payload.get("day_count_method", "ACT/365"),
        compounding_method=payload.get("compounding_method", "compound"),
        interpolation_method=payload.get("interpolation_method", "pchip"),
        extrapolation_method=payload.get("extrapolation_method", "flat"),
        display_unit=payload.get("display_unit", "percent"),
        point_unit=payload.get("point_unit", "percent"),
        precision_digits=payload.get("precision_digits", 4),
        is_real_time=payload.get("is_real_time", 0),
        tenor_set_json=payload.get("tenor_set", []),
        source_id=payload.get("source_id"),
        description=payload.get("description", ""),
        owner_role=payload.get("owner_role", ""),
        created_by=str(user.get("id", "")),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # 根据 tenor_set 自动同步曲线点（rate_value 留空）
    point_unit = payload.get("point_unit", "percent")
    added = _sync_curve_points(
        db, curve_code=row.code,
        tenor_set=payload.get("tenor_set", []),
        point_unit=point_unit,
        created_by=str(user.get("id", "")),
    )
    db.commit()

    return ResponseBase(data={
        "id": row.id, "code": row.code, "auto_added_points": added,
    }, message=f"曲线已创建，自动初始化 {added} 个期限点")


@router.put("/definitions/{code}", response_model=ResponseBase)
def update_definition(code: str, payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """更新曲线定义"""
    row = db.query(CurvCurveDefinition).filter(
        CurvCurveDefinition.code == code, CurvCurveDefinition.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="曲线不存在")
    editable = (
        "name", "curve_type", "curve_category", "category", "currency",
        "rate_type_code", "day_count_method", "compounding_method",
        "interpolation_method", "extrapolation_method",
        "display_unit", "point_unit", "precision_digits", "is_real_time",
        "source_id", "description", "owner_role",
    )
    for f in editable:
        if f in payload:
            setattr(row, f, payload[f])
    sync_points = False
    new_point_unit = row.point_unit
    if "tenor_set" in payload:
        row.tenor_set_json = payload["tenor_set"]
        sync_points = True
    if "point_unit" in payload:
        new_point_unit = payload["point_unit"]
        sync_points = True
    row.updated_by = str(user.get("id", ""))

    # 如果 tenor_set 或 point_unit 变更，同步点定义
    added = 0
    if sync_points:
        added = _sync_curve_points(
            db, curve_code=row.code,
            tenor_set=row.tenor_set_json or [],
            point_unit=new_point_unit,
            created_by=str(user.get("id", "")),
        )

    db.commit()
    return ResponseBase(data={"auto_added_points": added}, message="更新成功")


@router.delete("/definitions/{code}", response_model=ResponseBase)
def delete_definition(code: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """删除曲线定义（逻辑删除）"""
    row = db.query(CurvCurveDefinition).filter(
        CurvCurveDefinition.code == code, CurvCurveDefinition.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="曲线不存在")
    row.is_deleted = 1
    row.updated_by = str(user.get("id", ""))
    db.commit()
    return ResponseBase(message="删除成功")


# ============ 曲线点定义 ============

@router.get("/points", response_model=ResponseBase)
def list_points(
    curve_code: Optional[str] = None,
    point_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """曲线点定义列表"""
    q = db.query(CurvCurvePoint).filter(
        CurvCurvePoint.status == 1, CurvCurvePoint.is_deleted == 0,
    )
    if curve_code:
        q = q.filter(CurvCurvePoint.curve_code == curve_code)
    if point_type:
        q = q.filter(CurvCurvePoint.point_type == point_type)
    rows = q.order_by(CurvCurvePoint.curve_code, CurvCurvePoint.sort_order, CurvCurvePoint.tenor).all()
    return ResponseBase(data=[
        {
            "id": r.id, "curve_code": r.curve_code, "tenor": r.tenor,
            "rate_value": float(r.rate_value) if r.rate_value is not None else None,
            "point_unit": r.point_unit, "point_type": r.point_type,
            "sort_order": r.sort_order, "description": r.description,
        }
        for r in rows
    ])


@router.post("/points", response_model=ResponseBase)
def create_point(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """新建曲线点"""
    curve_code = payload.get("curve_code")
    tenor = payload.get("tenor")
    if not curve_code or not tenor:
        raise HTTPException(status_code=400, detail="curve_code 和 tenor 必填")
    existing = db.query(CurvCurvePoint).filter(
        CurvCurvePoint.curve_code == curve_code,
        CurvCurvePoint.tenor == tenor,
        CurvCurvePoint.point_type == payload.get("point_type", "standard"),
        CurvCurvePoint.is_deleted == 0,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"曲线点 {curve_code}/{tenor} 已存在")
    row = CurvCurvePoint(
        curve_code=curve_code,
        tenor=tenor,
        rate_value=payload.get("rate_value"),
        point_unit=payload.get("point_unit", "percent"),
        point_type=payload.get("point_type", "standard"),
        sort_order=payload.get("sort_order", 0),
        description=payload.get("description", ""),
        created_by=str(user.get("id", "")),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ResponseBase(data={"id": row.id, "curve_code": row.curve_code, "tenor": row.tenor})


@router.put("/points/{point_id}", response_model=ResponseBase)
def update_point(point_id: int, payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """更新曲线点"""
    row = db.query(CurvCurvePoint).filter(
        CurvCurvePoint.id == point_id, CurvCurvePoint.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="曲线点不存在")
    for f in ("tenor", "rate_value", "point_unit", "point_type", "sort_order", "description"):
        if f in payload:
            setattr(row, f, payload[f])
    db.commit()
    return ResponseBase(message="更新成功")


@router.delete("/points/{point_id}", response_model=ResponseBase)
def delete_point(point_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """删除曲线点"""
    row = db.query(CurvCurvePoint).filter(
        CurvCurvePoint.id == point_id, CurvCurvePoint.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="曲线点不存在")
    row.is_deleted = 1
    db.commit()
    return ResponseBase(message="删除成功")


@router.post("/points/batch", response_model=ResponseBase)
def batch_create_points(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """批量导入曲线点（用于快速配置）"""
    curve_code = payload.get("curve_code")
    points = payload.get("points", [])
    if not curve_code or not points:
        raise HTTPException(status_code=400, detail="curve_code 和 points 必填")
    inserted = 0
    updated = 0
    for p in points:
        tenor = p.get("tenor")
        if not tenor:
            continue
        existing = db.query(CurvCurvePoint).filter(
            CurvCurvePoint.curve_code == curve_code,
            CurvCurvePoint.tenor == tenor,
            CurvCurvePoint.point_type == p.get("point_type", "standard"),
            CurvCurvePoint.is_deleted == 0,
        ).first()
        if existing:
            existing.rate_value = p.get("rate_value", existing.rate_value)
            existing.point_unit = p.get("point_unit", existing.point_unit)
            existing.sort_order = p.get("sort_order", existing.sort_order)
            existing.description = p.get("description", existing.description)
            updated += 1
        else:
            db.add(CurvCurvePoint(
                curve_code=curve_code,
                tenor=tenor,
                rate_value=p.get("rate_value"),
                point_unit=p.get("point_unit", "percent"),
                point_type=p.get("point_type", "standard"),
                sort_order=p.get("sort_order", 0),
                description=p.get("description", ""),
                created_by=str(user.get("id", "")),
            ))
            inserted += 1
    db.commit()
    return ResponseBase(data={"inserted": inserted, "updated": updated})


# === 数据源 ===
@router.get("/data-sources", response_model=ResponseBase)
def list_data_sources(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.query(CurvDataSource).filter(CurvDataSource.status == 1, CurvDataSource.is_deleted == 0).all()
    return ResponseBase(data=[
        {
            "id": r.id, "code": r.code, "name": r.name, "source_type": r.source_type,
            "provider": r.provider, "frequency": r.frequency, "cron_expr": r.cron_expr,
            "is_enabled": r.is_enabled, "last_run_time": r.last_run_time.isoformat() if r.last_run_time else None,
            "last_run_status": r.last_run_status, "last_run_msg": r.last_run_msg,
        }
        for r in rows
    ])


# === 采集任务 ===
@router.get("/collection/tasks", response_model=ResponseBase)
def list_tasks(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.query(CurvCollectionTask).filter(CurvCollectionTask.status == 1, CurvCollectionTask.is_deleted == 0).all()
    return ResponseBase(data=[
        {
            "id": r.id, "task_code": r.task_code, "task_name": r.task_name,
            "source_id": r.source_id, "schedule_type": r.schedule_type,
            "cron_expr": r.cron_expr, "is_enabled": r.is_enabled,
        }
        for r in rows
    ])


@router.get("/collection/logs", response_model=ResponseBase)
def list_logs(
    limit: int = 50,
    task_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    q = db.query(CurvCollectionLog)
    if task_id:
        q = q.filter(CurvCollectionLog.task_id == task_id)
    rows = q.order_by(CurvCollectionLog.start_time.desc()).limit(limit).all()
    return ResponseBase(data=[
        {
            "id": r.id, "task_id": r.task_id, "source_id": r.source_id,
            "trade_date": r.trade_date.isoformat(), "start_time": r.start_time.isoformat(),
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "duration_ms": r.duration_ms, "status": r.status, "record_count": r.record_count,
            "error_msg": r.error_msg, "retry_count": r.retry_count,
        }
        for r in rows
    ])


# === 派生曲线 ===
@router.get("/derived", response_model=ResponseBase)
def list_derived(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.query(CurvDerivedCurve).filter(CurvDerivedCurve.status == 1, CurvDerivedCurve.is_deleted == 0).all()
    return ResponseBase(data=[
        {
            "id": r.id, "curve_code": r.curve_code, "name": r.name,
            "base_curves": r.base_curve_codes_json, "formula": r.formula,
            "formula_type": r.formula_type, "auto_update": r.auto_update,
        }
        for r in rows
    ])


# === 校验规则 ===
@router.get("/validation-rules", response_model=ResponseBase)
def list_rules(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.query(CurvValidationRule).filter(CurvValidationRule.status == 1, CurvValidationRule.is_deleted == 0).all()
    return ResponseBase(data=[
        {
            "id": r.id, "rule_code": r.rule_code, "rule_type": r.rule_type,
            "curve_code": r.curve_code, "rule_config": r.rule_config_json,
            "severity": r.severity, "is_enabled": r.is_enabled,
        }
        for r in rows
    ])


# === 插件模型 ===
@router.get("/plugins", response_model=ResponseBase)
def list_plugins(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.query(CurvPluginModel).filter(CurvPluginModel.is_enabled == 1).all()
    return ResponseBase(data=[
        {
            "id": r.id, "code": r.code, "name": r.name, "type": r.type,
            "impl_path": r.impl_path, "params_schema": r.params_schema,
            "description": r.description, "is_builtin": r.is_builtin,
        }
        for r in rows
    ])