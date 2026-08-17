"""插值算法"""
from typing import List
import numpy as np
from scipy.interpolate import CubicSpline as SciCubicSpline, PchipInterpolator


def _to_arrays(tenors: List[str], rates: List[float]):
    """把 tenor 字符串转换为天数"""
    tenor_to_days = {
        "1D": 1, "7D": 7, "14D": 14, "1M": 30, "3M": 90, "6M": 180,
        "9M": 270, "1Y": 365, "2Y": 730, "3Y": 365 * 3, "5Y": 365 * 5, "7Y": 365 * 7,
        "10Y": 365 * 10, "15Y": 365 * 15, "20Y": 365 * 20, "30Y": 365 * 30,
        "ON": 1, "1W": 7, "2W": 14,
    }
    xs = np.array([tenor_to_days.get(t, 365 * int(t.rstrip("Y")) if t.endswith("Y") else 30) for t in tenors], dtype=float)
    ys = np.array(rates, dtype=float)
    return xs, ys


def linear(tenors: List[str], rates: List[float], target_tenors: List[str]) -> List[float]:
    """线性插值"""
    xs, ys = _to_arrays(tenors, rates)
    tx, _ = _to_arrays(target_tenors, [0] * len(target_tenors))
    return list(np.interp(tx, xs, ys))


def log_linear(tenors: List[str], rates: List[float], target_tenors: List[str]) -> List[float]:
    """对数线性插值（贴现因子）"""
    xs, ys = _to_arrays(tenors, rates)
    tx, _ = _to_arrays(target_tenors, [0] * len(target_tenors))
    # 利率 -> 贴现因子 -> log线性插值 -> 利率
    df = np.exp(-ys / 100 * xs / 365)
    log_df = np.log(df)
    interp_log_df = np.interp(tx, xs, log_df)
    # 转回利率
    out = -(interp_log_df * 365 / tx) * 100
    return list(np.where(tx > 0, out, ys))


def cubic_spline(tenors: List[str], rates: List[float], target_tenors: List[str]) -> List[float]:
    """三次样条插值"""
    xs, ys = _to_arrays(tenors, rates)
    tx, _ = _to_arrays(target_tenors, [0] * len(target_tenors))
    cs = SciCubicSpline(xs, ys)
    return list(cs(tx))


def pchip(tenors: List[str], rates: List[float], target_tenors: List[str]) -> List[float]:
    """PCHIP 单调保形插值（适合利率曲线）"""
    xs, ys = _to_arrays(tenors, rates)
    tx, _ = _to_arrays(target_tenors, [0] * len(target_tenors))
    pchip_interp = PchipInterpolator(xs, ys)
    return list(pchip_interp(tx))


INTERPOLATORS = {
    "linear": linear,
    "log_linear": log_linear,
    "cubic_spline": cubic_spline,
    "pchip": pchip,
}