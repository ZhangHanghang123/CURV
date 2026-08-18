"""分析 API：走势、形态、利差、KRD"""
from datetime import date, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ResponseBase
from ..dependencies import get_current_user
from ..services import AnalyzerService

router = APIRouter(prefix="/api/analysis", tags=["分析建模"])


@router.get("/trend", response_model=ResponseBase)
def trend(
    curve_code: str,
    tenor: str,
    days: int = 365,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """单期限时序走势"""
    end = end_date or date.today()
    start = end - timedelta(days=days)
    svc = AnalyzerService(db)
    return ResponseBase(data=svc.get_trend(curve_code, tenor, start, end))


@router.get("/trend/multi", response_model=ResponseBase)
def trend_multi(
    curve_code: str,
    tenors: str,  # 逗号分隔: "1Y,5Y,10Y"
    days: int = 365,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """多期限叠加"""
    end = end_date or date.today()
    start = end - timedelta(days=days)
    tenor_list = [t.strip() for t in tenors.split(",")]
    svc = AnalyzerService(db)
    return ResponseBase(data=svc.get_multi_tenor_trend(curve_code, tenor_list, start, end))


@router.get("/spread", response_model=ResponseBase)
def spread(
    curve_code: str,
    long_tenor: str = "10Y",
    short_tenor: str = "1Y",
    trade_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """利差"""
    td = trade_date or date.today()
    svc = AnalyzerService(db)
    return ResponseBase(data=svc.compute_spread(curve_code, long_tenor, short_tenor, td))


@router.get("/shape-metrics", response_model=ResponseBase)
def shape_metrics(
    curve_code: str,
    trade_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """形态指标（单日快照）"""
    td = trade_date or date.today()
    svc = AnalyzerService(db)
    return ResponseBase(data=svc.shape_metrics(curve_code, td))


@router.get("/shape-metrics-trend", response_model=ResponseBase)
def shape_metrics_trend(
    curve_code: str,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """形态指标趋势（时间序列）"""
    svc = AnalyzerService(db)
    return ResponseBase(data=svc.shape_metrics_trend(curve_code, start_date, end_date))


@router.get("/krd", response_model=ResponseBase)
def krd(
    curve_code: str,
    trade_date: Optional[date] = None,
    shock_bp: float = 1.0,
    portfolio_value: float = 10000.0,
    duration: float = 5.0,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """关键利率久期"""
    td = trade_date or date.today()
    svc = AnalyzerService(db)
    res = svc.krd(curve_code, td, shock_bp=shock_bp, cashflow_amount=portfolio_value)
    res["duration"] = duration
    return ResponseBase(data=res)