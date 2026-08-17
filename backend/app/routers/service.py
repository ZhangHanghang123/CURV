"""对外标准服务 API（供 FTP / 估值 / ALM 调用）"""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ResponseBase
from ..services import BuildService

router = APIRouter(prefix="/api/service", tags=["对外服务"])


def check_api_key(x_api_key: Optional[str] = Header(None)):
    """API Key 鉴权（简化版，生产应做严格校验）"""
    # 这里先简化，生产环境应做严格校验 + 限流
    return x_api_key or "anonymous"


@router.get("/curve/{code}", response_model=ResponseBase)
def get_curve(
    code: str,
    trade_date: Optional[date] = None,
    version: str = "official",
    db: Session = Depends(get_db),
    api_key: str = Depends(check_api_key),
):
    """对外标准曲线查询服务（最常用）"""
    td = trade_date or date.today()
    svc = BuildService(db)
    rates = svc.get_curve(code, td, version)
    if not rates:
        raise HTTPException(status_code=404, detail="曲线数据未找到")
    return ResponseBase(data={
        "curve_code": code,
        "trade_date": td.isoformat(),
        "version": version,
        "tenors": list(rates.keys()),
        "rates": list(rates.values()),
    })


@router.post("/interpolate", response_model=ResponseBase)
def interpolate_service(
    payload: dict,
    db: Session = Depends(get_db),
    api_key: str = Depends(check_api_key),
):
    """自定义期限点插值"""
    curve_code = payload.get("curve_code")
    target_tenors = payload.get("target_tenors")
    method = payload.get("method", "pchip")
    trade_date_str = payload.get("trade_date")
    if not curve_code or not target_tenors or not trade_date_str:
        raise HTTPException(status_code=400, detail="缺少必要参数")

    td = date.fromisoformat(trade_date_str)
    svc = BuildService(db)
    res = svc.interpolate(curve_code, td, target_tenors, method)
    return ResponseBase(data=res)


@router.post("/discount-factor", response_model=ResponseBase)
def discount_factor(
    payload: dict,
    db: Session = Depends(get_db),
    api_key: str = Depends(check_api_key),
):
    """折现因子查询"""
    curve_code = payload.get("curve_code")
    tenors_days = payload.get("tenors_days")  # 期限天数列表
    trade_date_str = payload.get("trade_date")
    if not curve_code or not tenors_days or not trade_date_str:
        raise HTTPException(status_code=400, detail="缺少必要参数")

    td = date.fromisoformat(trade_date_str)
    svc = BuildService(db)
    rates = svc.get_curve(curve_code, td)
    if not rates:
        raise HTTPException(status_code=404, detail="曲线数据未找到")

    # 简单对数线性插值获取任意期限利率
    tenor_to_days = {
        "1D": 1, "7D": 7, "14D": 14, "1M": 30, "3M": 90, "6M": 180,
        "9M": 270, "1Y": 365, "2Y": 730, "3Y": 365 * 3, "5Y": 365 * 5, "7Y": 365 * 7,
        "10Y": 365 * 10, "15Y": 365 * 15, "20Y": 365 * 20, "30Y": 365 * 30,
    }
    sorted_items = sorted(rates.items(), key=lambda x: tenor_to_days.get(x[0], 0))
    xs = [tenor_to_days.get(t, 0) for t, _ in sorted_items]
    ys = [v for _, v in sorted_items]

    import numpy as np
    xs_arr = np.array(xs, dtype=float)
    ys_arr = np.array(ys, dtype=float)
    df_per_tenor = {}
    for t in tenors_days:
        if t in xs_arr:
            rate = float(np.interp(t, xs_arr, ys_arr))
        else:
            rate = float(np.interp(t, xs_arr, ys_arr))
        df = float(np.exp(-rate / 100 * t / 365))
        df_per_tenor[str(t)] = round(df, 8)

    return ResponseBase(data={
        "curve_code": curve_code,
        "trade_date": td.isoformat(),
        "discount_factors": df_per_tenor,
    })