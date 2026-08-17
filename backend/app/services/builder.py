"""曲线构建服务：拼接、拟合、插值"""
from datetime import date
from typing import List, Dict, Optional
import json

from sqlalchemy.orm import Session

from ..models import CurvRateData, CurvFittingParam, CurvCurveDefinition
from ..engines import fitting as fit_eng, interpolation as interp_eng


class BuildService:
    def __init__(self, db: Session):
        self.db = db

    def get_curve(self, curve_code: str, trade_date: date, version: str = "official") -> Dict[str, float]:
        """读取一条曲线的全部期限点（按期限顺序排序）"""
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
        sorted_rows = sorted(rows, key=lambda x: tenor_to_days.get(str(x.tenor), 0))
        return {r.tenor: float(r.rate_value) for r in sorted_rows}

    def splice(
        self,
        short_curve_code: str,
        long_curve_code: str,
        trade_date: date,
        splice_tenor: str = "1Y",
        mode: str = "linear_transition",
        version: str = "official",
    ) -> Dict:
        """拼接两条曲线（短端 + 长端）"""
        short = self.get_curve(short_curve_code, trade_date, version)
        long_ = self.get_curve(long_curve_code, trade_date, version)
        if not short or not long_:
            return {"error": "short or long curve empty", "short": short, "long": long_}

        # 简化：直接拼接，重叠区间按 mode 处理
        tenor_to_days = {
            "1D": 1, "7D": 7, "14D": 14, "1M": 30, "3M": 90, "6M": 180,
            "9M": 270, "1Y": 365, "2Y": 730, "3Y": 365 * 3, "5Y": 365 * 5, "7Y": 365 * 7,
            "10Y": 365 * 10, "15Y": 365 * 15, "20Y": 365 * 20, "30Y": 365 * 30,
        }
        splice_days = tenor_to_days.get(splice_tenor, 365)

        result = {}
        for tenor, rate in short.items():
            days = tenor_to_days.get(tenor, 365)
            if days <= splice_days:
                result[tenor] = rate

        # 拼接点附近短端/长端重合区
        for tenor, rate in long_.items():
            days = tenor_to_days.get(tenor, 365)
            if days >= splice_days:
                result[tenor] = rate

        # 按期限排序
        sorted_items = sorted(result.items(), key=lambda x: tenor_to_days.get(x[0], 0))

        return {
            "splice_tenor": splice_tenor,
            "mode": mode,
            "short_curve": short_curve_code,
            "long_curve": long_curve_code,
            "trade_date": trade_date.isoformat(),
            "tenors": [t for t, _ in sorted_items],
            "rates": [r for _, r in sorted_items],
        }

    def fit(
        self,
        curve_code: str,
        trade_date: date,
        model: str = "nelson_siegel",
        version: str = "official",
        operator: str = "system",
    ) -> Dict:
        """拟合一条曲线"""
        tenors_rates = self.get_curve(curve_code, trade_date, version)
        if len(tenors_rates) < 4:
            return {"error": "曲线期限点不足，至少需要 4 个"}

        # 按期限排序
        tenor_to_days = {
            "1D": 1, "7D": 7, "14D": 14, "1M": 30, "3M": 90, "6M": 180,
            "9M": 270, "1Y": 365, "2Y": 730, "3Y": 365 * 3, "5Y": 365 * 5, "7Y": 365 * 7,
            "10Y": 365 * 10, "15Y": 365 * 15, "20Y": 365 * 20, "30Y": 365 * 30,
        }
        sorted_items = sorted(tenors_rates.items(), key=lambda x: tenor_to_days.get(x[0], 0))
        tenors = [t for t, _ in sorted_items]
        rates = [r for _, r in sorted_items]

        result = fit_eng.fit_model(model, tenors, rates)

        # 持久化拟合参数
        params = json.dumps(result["params"], ensure_ascii=False)
        row = CurvFittingParam(
            curve_code=curve_code,
            trade_date=trade_date,
            version_no=version,
            model_code=model,
            params_json=result["params"],
            rmse=result["rmse_bp"],
            r2=result["r2"],
            max_residual_bp=max(abs(x) for x in result["residuals_bp"]) if result["residuals_bp"] else 0,
            residual_summary_json={"values": result["residuals_bp"]},
            fit_status="success",
            fit_duration_ms=0,
            operator=operator,
        )
        # upsert
        existing = (
            self.db.query(CurvFittingParam)
            .filter(
                CurvFittingParam.curve_code == curve_code,
                CurvFittingParam.trade_date == trade_date,
                CurvFittingParam.version_no == version,
                CurvFittingParam.model_code == model,
            )
            .first()
        )
        if existing:
            existing.params_json = result["params"]
            existing.rmse = result["rmse_bp"]
            existing.r2 = result["r2"]
            existing.max_residual_bp = row.max_residual_bp
            existing.residual_summary_json = row.residual_summary_json
            existing.operator = operator
        else:
            self.db.add(row)
        self.db.commit()

        return result

    def interpolate(
        self,
        curve_code: str,
        trade_date: date,
        target_tenors: List[str],
        method: str = "pchip",
        version: str = "official",
    ) -> Dict:
        """插值"""
        tenors_rates = self.get_curve(curve_code, trade_date, version)
        if len(tenors_rates) < 2:
            return {"error": "曲线期限点不足"}

        tenor_to_days = {
            "1D": 1, "7D": 7, "14D": 14, "1M": 30, "3M": 90, "6M": 180,
            "9M": 270, "1Y": 365, "2Y": 730, "3Y": 365 * 3, "5Y": 365 * 5, "7Y": 365 * 7,
            "10Y": 365 * 10, "15Y": 365 * 15, "20Y": 365 * 20, "30Y": 365 * 30,
        }
        sorted_items = sorted(tenors_rates.items(), key=lambda x: tenor_to_days.get(x[0], 0))
        tenors = [t for t, _ in sorted_items]
        rates = [r for _, r in sorted_items]

        interp_fn = interp_eng.INTERPOLATORS.get(method)
        if not interp_fn:
            return {"error": f"unsupported method: {method}"}

        out_rates = interp_fn(tenors, rates, target_tenors)
        return {
            "curve_code": curve_code,
            "trade_date": trade_date.isoformat(),
            "method": method,
            "target_tenors": target_tenors,
            "rates": out_rates,
        }