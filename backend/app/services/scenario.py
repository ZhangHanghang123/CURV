"""情景模拟与压力测试"""
from datetime import date
from typing import Dict, List, Optional
import json
import uuid
from sqlalchemy.orm import Session

from ..models import CurvRateData, CurvScenario, CurvScenarioResult


class ScenarioService:
    def __init__(self, db: Session):
        self.db = db

    def list_scenarios(self) -> List[Dict]:
        rows = self.db.query(CurvScenario).filter(CurvScenario.is_enabled == 1, CurvScenario.status == 1).all()
        return [
            {
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "scenario_type": r.scenario_type,
                "shock_json": r.shock_json,
                "historical_date": r.historical_date.isoformat() if r.historical_date else None,
                "is_preset": r.is_preset,
                "description": r.description,
            }
            for r in rows
        ]

    def apply_shock(self, curve_code: str, trade_date: date, scenario_type: str, shock: Dict, version: str = "official") -> Dict:
        """对一条曲线施加冲击，返回新曲线"""
        rows = (
            self.db.query(CurvRateData)
            .filter(
                CurvRateData.curve_code == curve_code,
                CurvRateData.trade_date == trade_date,
                CurvRateData.source_version == version,
                CurvRateData.data_status == "active",
            )
            .all()
        )
        tenor_to_days = {
            "1D": 1, "7D": 7, "14D": 14, "ON": 1, "1W": 7, "2W": 14,
            "1M": 30, "3M": 90, "6M": 180, "9M": 270, "1Y": 365, "2Y": 730,
            "3Y": 365 * 3, "5Y": 365 * 5, "7Y": 365 * 7,
            "10Y": 365 * 10, "15Y": 365 * 15, "20Y": 365 * 20, "30Y": 365 * 30,
        }
        original = {}
        for r in rows:
            original[r.tenor] = float(r.rate_value)

        if not original:
            return {"error": "curve empty"}

        shocked = {}
        if scenario_type == "parallel":
            bp = float(shock.get("shock_bp", 0))
            for t, v in original.items():
                shocked[t] = v + bp / 100
        elif scenario_type == "steepener":
            short_bp = float(shock.get("short_bp", 0))
            long_bp = float(shock.get("long_bp", 0))
            for t, v in original.items():
                days = tenor_to_days.get(t, 365)
                # 线性插值权重
                w = min(1.0, days / 3650.0)  # 10Y 以上 = 1
                shocked[t] = v + (short_bp * (1 - w) + long_bp * w) / 100
        elif scenario_type == "flattener":
            short_bp = float(shock.get("short_bp", 0))
            long_bp = float(shock.get("long_bp", 0))
            for t, v in original.items():
                days = tenor_to_days.get(t, 365)
                w = min(1.0, days / 3650.0)
                shocked[t] = v + (long_bp * (1 - w) + short_bp * w) / 100
        else:
            # 暂不支持历史/自定义，返回原曲线
            shocked = dict(original)

        return {
            "curve_code": curve_code,
            "trade_date": trade_date.isoformat(),
            "scenario_type": scenario_type,
            "shock": shock,
            "original": original,
            "shocked": shocked,
        }

    def run_scenario(
        self,
        scenario_id: int,
        curve_code: str,
        trade_date: date,
        asset_liability_name: str = "债券组合",
        portfolio_value: float = 10000.0,  # 万元
        duration: float = 5.0,
        version: str = "official",
    ) -> Dict:
        """运行情景并计算 PV/NII/EVE 变化（简化模型）"""
        scenario = self.db.query(CurvScenario).filter(CurvScenario.id == scenario_id).first()
        if not scenario:
            return {"error": "scenario not found"}

        shock_res = self.apply_shock(curve_code, trade_date, scenario.scenario_type, scenario.shock_json, version)
        if "error" in shock_res:
            return shock_res

        # 计算冲击幅度
        if scenario.scenario_type == "parallel":
            shock_bp = float(scenario.shock_json.get("shock_bp", 0))
        elif scenario.scenario_type in ("steepener", "flattener"):
            shock_bp = float(scenario.shock_json.get("short_bp", 0))
        else:
            shock_bp = 0

        # PV 变化：- PV * duration * shock_bp / 10000
        pv_change = -portfolio_value * duration * shock_bp / 10000
        pv_change_pct = pv_change / portfolio_value * 100

        # NII 变化：+ PV * shock_bp / 10000（短期）
        nii_change = portfolio_value * shock_bp / 10000 * 0.5  # 简化假设
        nii_change_pct = nii_change / portfolio_value * 100

        # EVE = PV
        eve_change = pv_change
        eve_change_pct = pv_change_pct

        run_code = f"RUN-{uuid.uuid4().hex[:8].upper()}"

        result = CurvScenarioResult(
            scenario_id=scenario_id,
            scenario_run_code=run_code,
            curve_code=curve_code,
            trade_date=trade_date,
            asset_liability_id=f"PF-{uuid.uuid4().hex[:6]}",
            asset_liability_name=asset_liability_name,
            base_value=portfolio_value,
            shocked_value=portfolio_value + pv_change,
            pv_change=round(pv_change, 4),
            pv_change_pct=round(pv_change_pct, 6),
            nii_change=round(nii_change, 4),
            nii_change_pct=round(nii_change_pct, 6),
            eve_change=round(eve_change, 4),
            eve_change_pct=round(eve_change_pct, 6),
            krd_vector_json={"duration": duration},
            details_json=shock_res,
            run_time_ms=0,
        )
        self.db.add(result)
        self.db.commit()

        return {
            "scenario_run_code": run_code,
            "scenario_id": scenario_id,
            "scenario_name": scenario.name,
            "curve_code": curve_code,
            "trade_date": trade_date.isoformat(),
            "base_value": portfolio_value,
            "shocked_value": portfolio_value + pv_change,
            "pv_change": round(pv_change, 4),
            "pv_change_pct": round(pv_change_pct, 4),
            "nii_change": round(nii_change, 4),
            "nii_change_pct": round(nii_change_pct, 4),
            "eve_change": round(eve_change, 4),
            "eve_change_pct": round(eve_change_pct, 4),
            "shocked_curve": shock_res["shocked"],
        }