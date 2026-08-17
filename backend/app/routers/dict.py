"""字典管理 API（沿用 ALMD sys_dict_type / sys_dict_data 模式）"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..schemas import ResponseBase
from ..dependencies import get_current_user
from ..models import SysDictType, SysDictData

router = APIRouter(prefix="/api/dict", tags=["字典管理"])


# ============ 字典类型 ============

@router.get("/types", response_model=ResponseBase)
def list_types(
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """字典类型列表（含码值数量）"""
    q = db.query(SysDictType).filter(
        SysDictType.status == 1, SysDictType.is_deleted == 0
    )
    if keyword:
        q = q.filter(
            (SysDictType.dict_code.contains(keyword)) |
            (SysDictType.dict_name.contains(keyword))
        )
    types = q.order_by(SysDictType.sort_order, SysDictType.id).all()
    data = []
    for t in types:
        cnt = db.query(SysDictData).filter(
            SysDictData.dict_type_id == t.id,
            SysDictData.status == 1,
            SysDictData.is_deleted == 0,
        ).count()
        data.append({
            "id": t.id,
            "dict_code": t.dict_code,
            "dict_name": t.dict_name,
            "description": t.description,
            "sort_order": t.sort_order,
            "status": t.status,
            "data_count": cnt,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return ResponseBase(data=data)


@router.get("/types/{type_id}", response_model=ResponseBase)
def get_type(type_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    row = db.query(SysDictType).filter(
        SysDictType.id == type_id, SysDictType.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    return ResponseBase(data={
        "id": row.id, "dict_code": row.dict_code, "dict_name": row.dict_name,
        "description": row.description, "sort_order": row.sort_order, "status": row.status,
    })


@router.post("/types", response_model=ResponseBase)
def create_type(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """新建字典类型"""
    code = payload.get("dict_code")
    name = payload.get("dict_name")
    if not code or not name:
        raise HTTPException(status_code=400, detail="dict_code 和 dict_name 必填")
    existing = db.query(SysDictType).filter(SysDictType.dict_code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"字典编码 {code} 已存在")
    row = SysDictType(
        dict_code=code,
        dict_name=name,
        description=payload.get("description", ""),
        sort_order=payload.get("sort_order", 0),
        status=payload.get("status", 1),
        created_by=user.get("id"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ResponseBase(data={"id": row.id, "dict_code": row.dict_code})


@router.put("/types/{type_id}", response_model=ResponseBase)
def update_type(type_id: int, payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    row = db.query(SysDictType).filter(
        SysDictType.id == type_id, SysDictType.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    for f in ("dict_name", "description", "sort_order", "status"):
        if f in payload:
            setattr(row, f, payload[f])
    row.updated_by = user.get("id")
    db.commit()
    return ResponseBase(message="更新成功")


@router.delete("/types/{type_id}", response_model=ResponseBase)
def delete_type(type_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    row = db.query(SysDictType).filter(
        SysDictType.id == type_id, SysDictType.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    row.is_deleted = 1
    # 同时逻辑删除码值
    db.query(SysDictData).filter(
        SysDictData.dict_type_id == type_id
    ).update({"is_deleted": 1})
    db.commit()
    return ResponseBase(message="删除成功")


# ============ 字典码值 ============

@router.get("/data", response_model=ResponseBase)
def list_data(
    dict_code: Optional[str] = None,
    dict_type_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """字典码值列表"""
    q = db.query(SysDictData).filter(
        SysDictData.status == 1, SysDictData.is_deleted == 0
    )
    if dict_code:
        type_row = db.query(SysDictType).filter(
            SysDictType.dict_code == dict_code, SysDictType.is_deleted == 0
        ).first()
        if not type_row:
            return ResponseBase(data=[])
        q = q.filter(SysDictData.dict_type_id == type_row.id)
    if dict_type_id:
        q = q.filter(SysDictData.dict_type_id == dict_type_id)
    if keyword:
        q = q.filter(
            (SysDictData.dict_label.contains(keyword)) |
            (SysDictData.dict_key.contains(keyword)) |
            (SysDictData.dict_value.contains(keyword))
        )
    rows = q.order_by(SysDictData.sort_order, SysDictData.id).all()
    return ResponseBase(data=[
        {
            "id": r.id, "dict_type_id": r.dict_type_id,
            "dict_key": r.dict_key, "dict_label": r.dict_label, "dict_value": r.dict_value,
            "is_default": r.is_default, "sort_order": r.sort_order, "status": r.status,
            "css_class": r.css_class, "list_class": r.list_class,
            "description": r.description,
        }
        for r in rows
    ])


@router.get("/data/all", response_model=ResponseBase)
def list_all_data(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """全部字典码值（按类型 code 分组，前端一次性缓存）"""
    types = db.query(SysDictType).filter(
        SysDictType.status == 1, SysDictType.is_deleted == 0
    ).order_by(SysDictType.sort_order).all()

    result = {}
    for t in types:
        items = db.query(SysDictData).filter(
            SysDictData.dict_type_id == t.id,
            SysDictData.status == 1,
            SysDictData.is_deleted == 0,
        ).order_by(SysDictData.sort_order).all()
        result[t.dict_code] = {
            "dict_name": t.dict_name,
            "items": [
                {
                    "key": r.dict_key, "label": r.dict_label, "value": r.dict_value,
                    "is_default": bool(r.is_default), "list_class": r.list_class,
                    "description": r.description,
                }
                for r in items
            ],
        }
    return ResponseBase(data=result)


@router.post("/data", response_model=ResponseBase)
def create_data(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """新建字典码值"""
    dict_code = payload.get("dict_code")
    key = payload.get("dict_key")
    label = payload.get("dict_label")
    if not dict_code or not key or not label:
        raise HTTPException(status_code=400, detail="dict_code/dict_key/dict_label 必填")
    type_row = db.query(SysDictType).filter(
        SysDictType.dict_code == dict_code, SysDictType.is_deleted == 0
    ).first()
    if not type_row:
        raise HTTPException(status_code=404, detail=f"字典类型 {dict_code} 不存在")
    existing = db.query(SysDictData).filter(
        SysDictData.dict_type_id == type_row.id,
        SysDictData.dict_key == key,
        SysDictData.is_deleted == 0,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"键 {key} 已存在")
    row = SysDictData(
        dict_type_id=type_row.id,
        dict_key=key,
        dict_label=label,
        dict_value=payload.get("dict_value", key),
        css_class=payload.get("css_class", ""),
        list_class=payload.get("list_class", ""),
        is_default=payload.get("is_default", 0),
        sort_order=payload.get("sort_order", 0),
        status=payload.get("status", 1),
        description=payload.get("description", ""),
        created_by=user.get("id"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ResponseBase(data={"id": row.id, "dict_key": row.dict_key})


@router.put("/data/{data_id}", response_model=ResponseBase)
def update_data(data_id: int, payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    row = db.query(SysDictData).filter(
        SysDictData.id == data_id, SysDictData.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="字典码值不存在")
    for f in ("dict_label", "dict_value", "is_default", "sort_order", "status", "css_class", "list_class", "description"):
        if f in payload:
            setattr(row, f, payload[f])
    row.updated_by = user.get("id")
    db.commit()
    return ResponseBase(message="更新成功")


@router.delete("/data/{data_id}", response_model=ResponseBase)
def delete_data(data_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    row = db.query(SysDictData).filter(
        SysDictData.id == data_id, SysDictData.is_deleted == 0
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="字典码值不存在")
    row.is_deleted = 1
    row.updated_by = user.get("id")
    db.commit()
    return ResponseBase(message="删除成功")