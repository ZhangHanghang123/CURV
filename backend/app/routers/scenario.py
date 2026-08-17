"""情景模拟 API"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ResponseBase
from ..dependencies import get_current_user
from ..services import ScenarioService

router = APIRouter(prefix="/api/scenario", tags=["情景模拟"])


@router.get("/list", response_model=ResponseBase)
def list_scenarios(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """预置情景列表"""
    svc = ScenarioService(db)
    return ResponseBase(data=svc.list_scenarios())


@router.post("/apply", response_model=ResponseBase)
def apply_shock(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """应用情景冲击到曲线（不计算结果）"""
    curve_code = payload.get("curve_code")
    trade_date_str = payload.get("trade_date")
    scenario_type = payload.get("scenario_type", "parallel")
    shock = payload.get("shock", {})
    if not curve_code or not trade_date_str:
        raise HTTPException(status_code=400, detail="缺少必要参数")
    svc = ScenarioService(db)
    res = svc.apply_shock(curve_code, date.fromisoformat(trade_date_str), scenario_type, shock)
    return ResponseBase(data=res)


@router.post("/run", response_model=ResponseBase)
def run_scenario(payload: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """运行情景模拟（计算 PV/NII/EVE 变化）"""
    scenario_id = payload.get("scenario_id")
    curve_code = payload.get("curve_code")
    trade_date_str = payload.get("trade_date")
    if not scenario_id or not curve_code or not trade_date_str:
        raise HTTPException(status_code=400, detail="缺少必要参数")
    svc = ScenarioService(db)
    res = svc.run_scenario(
        scenario_id=int(scenario_id),
        curve_code=curve_code,
        trade_date=date.fromisoformat(trade_date_str),
        asset_liability_name=payload.get("asset_liability_name", "债券组合"),
        portfolio_value=float(payload.get("portfolio_value", 10000.0)),
        duration=float(payload.get("duration", 5.0)),
    )
    return ResponseBase(data=res)