"""分析服务：走势、形态、利差"""
from datetime import date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import CurvRateData


class AnalyzerService:
    def __init__(self, db: Session):
        self.db = db

    def get_trend(
        self,
        curve_code: str,
        tenor: str,
        start_date: date,
        end_date: date,
        version: str = "official",
    ) -> Dict:
        """单期限时序走势"""
        rows = (
            self.db.query(CurvRateData)
            .filter(
                CurvRateData.curve_code == curve_code,
                CurvRateData.tenor == tenor,
                CurvRateData.source_version == version,
                CurvRateData.trade_date.between(start_date, end_date),
                CurvRateData.data_status == "active",
            )
            .order_by(CurvRateData.trade_date)
            .all()
        )
        dates = [r.trade_date.isoformat() for r in rows]
        rates = [float(r.rate_value) for r in rows]
        if not rates:
            return {"dates": [], "rates": [], "stats": {}}

        import numpy as np
        arr = np.array(rates)
        stats = {
            "mean": float(arr.mean()),
            "median": float(np.median(arr)),
            "max": float(arr.max()),
            "min": float(arr.min()),
            "std": float(arr.std()),
            "count": len(arr),
        }
        # 年化波动率：日波动率 * sqrt(252)
        if len(arr) > 1:
            daily_ret = np.diff(arr)
            stats["annual_volatility"] = float(daily_ret.std() * (252 ** 0.5))
        else:
            stats["annual_volatility"] = 0.0

        return {
            "curve_code": curve_code,
            "tenor": tenor,
            "dates": dates,
            "rates": rates,
            "stats": stats,
        }

    def get_multi_tenor_trend(
        self,
        curve_code: str,
        tenors: List[str],
        start_date: date,
        end_date: date,
        version: str = "official",
    ) -> Dict:
        """多期限叠加走势"""
        rows = (
            self.db.query(CurvRateData)
            .filter(
                CurvRateData.curve_code == curve_code,
                CurvRateData.tenor.in_(tenors),
                CurvRateData.source_version == version,
                CurvRateData.trade_date.between(start_date, end_date),
                CurvRateData.data_status == "active",
            )
            .order_by(CurvRateData.trade_date)
            .all()
        )
        # pivot
        pivot: Dict[str, Dict[str, float]] = {}
        for r in rows:
            pivot.setdefault(r.trade_date.isoformat(), {})[r.tenor] = float(r.rate_value)

        dates = sorted(pivot.keys())
        return {
            "curve_code": curve_code,
            "tenors": tenors,
            "dates": dates,
            "series": {t: [pivot.get(d, {}).get(t) for d in dates] for t in tenors},
        }

    def compute_spread(self, curve_code: str, long_tenor: str, short_tenor: str, trade_date: date, version: str = "official") -> Dict:
        """利差计算（如 10Y-1Y）"""
        rows = (
            self.db.query(CurvRateData)
            .filter(
                CurvRateData.curve_code == curve_code,
                CurvRateData.tenor.in_([long_tenor, short_tenor]),
                CurvRateData.trade_date == trade_date,
                CurvRateData.source_version == version,
                CurvRateData.data_status == "active",
            )
            .all()
        )
        rates = {r.tenor: float(r.rate_value) for r in rows}
        if long_tenor not in rates or short_tenor not in rates:
            return {"error": f"missing tenor", "available": list(rates.keys())}
        spread_bp = (rates[long_tenor] - rates[short_tenor]) * 100
        return {
            "curve_code": curve_code,
            "trade_date": trade_date.isoformat(),
            "long_tenor": long_tenor,
            "short_tenor": short_tenor,
            "long_rate": rates[long_tenor],
            "short_rate": rates[short_tenor],
            "spread_bp": round(spread_bp, 2),
        }

    def shape_metrics(self, curve_code: str, trade_date: date, version: str = "official") -> Dict:
        """形态指标：长短期利差 / 信用利差 / 斜率 / 曲率 / 倒挂"""
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
        rates = {r.tenor: float(r.rate_value) for r in rows}

        metrics = {}

        def spread(a, b):
            if a in rates and b in rates:
                return round((rates[a] - rates[b]) * 100, 2)
            return None

        metrics["spread_10y_1y"] = spread("10Y", "1Y")
        metrics["spread_10y_5y"] = spread("10Y", "5Y")
        metrics["spread_5y_1y"] = spread("5Y", "1Y")

        # 倒挂识别：短端 > 长端
        if "1Y" in rates and "10Y" in rates:
            metrics["inversion"] = rates["1Y"] > rates["10Y"]

        # 信用利差（如果有企业债数据）
        corp_rows = (
            self.db.query(CurvRateData)
            .filter(
                CurvRateData.curve_code == "cnb_corp_aaa",
                CurvRateData.tenor == "5Y",
                CurvRateData.trade_date == trade_date,
                CurvRateData.source_version == version,
            )
            .first()
        )
        if corp_rows and "5Y" in rates:
            metrics["credit_spread_aaa_5y_bp"] = round((float(corp_rows.rate_value) - rates["5Y"]) * 100, 2)

        return {
            "curve_code": curve_code,
            "trade_date": trade_date.isoformat(),
            "metrics": metrics,
        }

    def krd(
        self,
        curve_code: str,
        trade_date: date,
        shock_bp: float = 1.0,
        key_tenors: Optional[List[str]] = None,
        cashflow_amount: float = 10000.0,
        version: str = "official",
    ) -> Dict:
        """关键利率久期（KRD）模拟"""
        key_tenors = key_tenors or ["3M", "1Y", "3Y", "5Y", "10Y", "30Y"]
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
        rates = {r.tenor: float(r.rate_value) for r in rows}
        tenor_to_days = {"3M": 90, "1Y": 365, "2Y": 730, "3Y": 365 * 3, "5Y": 365 * 5, "10Y": 365 * 10, "30Y": 365 * 30}

        base_pv = cashflow_amount
        krd_vector = {}
        pv01_vector = {}
        for t in key_tenors:
            if t in rates:
                # 简化：久期 = 期限年数
                duration_years = tenor_to_days.get(t, 365) / 365.0
                # DV01 近似 = -PV * duration * shock_bp / 10000
                dv01 = base_pv * duration_years * shock_bp / 10000
                pv01_vector[t] = round(dv01, 2)
                krd_vector[t] = round(duration_years * 100, 4) / 100  # 转换为年（如 3.85）
            else:
                krd_vector[t] = None
                pv01_vector[t] = None

        total_dv01 = sum(v for v in pv01_vector.values() if v is not None)

        return {
            "curve_code": curve_code,
            "trade_date": trade_date.isoformat(),
            "shock_bp": shock_bp,
            "krd_vector": krd_vector,
            "pv01_vector": pv01_vector,
            "total_dv01": round(total_dv01, 2),
        }