"""曲线构建引擎 API（拼接、插值、平滑、拟合）"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ResponseBase
from ..dependencies import get_current_user
from ..services import BuildService

router = APIRouter(prefix="/api/build", tags=["曲线构建"])


@router.post("/splice", response_model=ResponseBase)
def splice(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """拼接短端 + 长端"""
    short = payload.get("short_curve")
    long_ = payload.get("long_curve")
    trade_date_str = payload.get("trade_date")
    if not short or not long_ or not trade_date_str:
        raise HTTPException(status_code=400, detail="缺少必要参数")

    svc = BuildService(db)
    res = svc.splice(
        short_curve_code=short,
        long_curve_code=long_,
        trade_date=date.fromisoformat(trade_date_str),
        splice_tenor=payload.get("splice_tenor", "1Y"),
        mode=payload.get("mode", "linear_transition"),
        version=payload.get("version", "official"),
    )
    return ResponseBase(data=res)


@router.post("/fit", response_model=ResponseBase)
def fit(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """曲线拟合（Nelson-Siegel / Svensson）"""
    curve_code = payload.get("curve_code")
    trade_date_str = payload.get("trade_date")
    model = payload.get("model", "nelson_siegel")
    if not curve_code or not trade_date_str:
        raise HTTPException(status_code=400, detail="缺少必要参数")

    svc = BuildService(db)
    res = svc.fit(
        curve_code=curve_code,
        trade_date=date.fromisoformat(trade_date_str),
        model=model,
        version=payload.get("version", "official"),
        operator=user.get("username", "system"),
    )
    return ResponseBase(data=res)


@router.post("/interpolate", response_model=ResponseBase)
def interpolate(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """插值"""
    curve_code = payload.get("curve_code")
    trade_date_str = payload.get("trade_date")
    target_tenors = payload.get("target_tenors")
    method = payload.get("method", "pchip")
    if not curve_code or not trade_date_str or not target_tenors:
        raise HTTPException(status_code=400, detail="缺少必要参数")

    svc = BuildService(db)
    res = svc.interpolate(
        curve_code=curve_code,
        trade_date=date.fromisoformat(trade_date_str),
        target_tenors=target_tenors,
        method=method,
        version=payload.get("version", "official"),
    )
    return ResponseBase(data=res)