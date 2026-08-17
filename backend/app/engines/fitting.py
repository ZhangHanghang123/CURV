"""曲线拟合：Nelson-Siegel / Svensson"""
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.optimize import minimize


def _to_days(tenors: List[str]) -> np.ndarray:
    tenor_to_days = {
        "1D": 1, "7D": 7, "14D": 14, "1M": 30, "3M": 90, "6M": 180,
        "9M": 270, "1Y": 365, "2Y": 730, "3Y": 365 * 3, "5Y": 365 * 5, "7Y": 365 * 7,
        "10Y": 365 * 10, "15Y": 365 * 15, "20Y": 365 * 20, "30Y": 365 * 30,
        "ON": 1, "1W": 7, "2W": 14,
    }
    return np.array([tenor_to_days.get(t, 365 * int(t.rstrip("Y")) if t.endswith("Y") else 30) for t in tenors], dtype=float)


def _ns_basis(t: np.ndarray, tau: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Nelson-Siegel 基函数（t 单位为年）"""
    t = t / 365.0  # 转为年
    x = t / tau
    # 避免 0 除
    x = np.where(x == 0, 1e-10, x)
    exp_x = np.exp(-x)
    factor = (1 - exp_x) / x
    level = np.ones_like(t)
    slope = factor
    curvature = factor - exp_x
    return level, slope, curvature


def _nss_basis(t: np.ndarray, tau1: float, tau2: float) -> Tuple[np.ndarray, ...]:
    """Svensson 基函数 = NS + 额外曲率项"""
    b0, b1, b2 = _ns_basis(t, tau1)
    t = t / 365.0
    x = t / tau2
    x = np.where(x == 0, 1e-10, x)
    exp_x = np.exp(-x)
    factor = (1 - exp_x) / x
    b3 = factor - exp_x
    return b0, b1, b2, b3


def _ns_predict(params: np.ndarray, t: np.ndarray) -> np.ndarray:
    beta0, beta1, beta2, tau = params
    b0, b1, b2 = _ns_basis(t, tau)
    return beta0 * b0 + beta1 * b1 + beta2 * b2


def _nss_predict(params: np.ndarray, t: np.ndarray) -> np.ndarray:
    beta0, beta1, beta2, beta3, tau1, tau2 = params
    b0, b1, b2, b3 = _nss_basis(t, tau1, tau2)
    return beta0 * b0 + beta1 * b1 + beta2 * b2 + beta3 * b3


def _loss(params, predict_fn, t, y):
    return np.sum((predict_fn(params, t) - y) ** 2)


def nelson_siegel(tenors: List[str], rates: List[float], tau0: float = 1.5) -> Dict:
    """Nelson-Siegel 拟合

    Returns:
        dict: {
            "params": {"beta0":..., "beta1":..., "beta2":..., "tau":...},
            "rmse": float (bp),
            "r2": float,
            "fitted": [...],
            "residuals_bp": [...],
            "tenors": [...]
        }
    """
    t = _to_days(tenors)
    y = np.array(rates, dtype=float)

    # 初值估计
    beta0_0 = y[-1]
    beta1_0 = y[0] - beta0_0
    beta2_0 = 0.0
    x0 = [beta0_0, beta1_0, beta2_0, tau0]

    res = minimize(_loss, x0, args=(_ns_predict, t, y), method="Nelder-Mead", options={"xatol": 1e-8, "fatol": 1e-10})
    beta0, beta1, beta2, tau = res.x

    fitted = _ns_predict(res.x, t)
    residuals = y - fitted
    rmse_bp = float(np.sqrt(np.mean(residuals ** 2)) * 100)
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "model": "nelson_siegel",
        "params": {"beta0": float(beta0), "beta1": float(beta1), "beta2": float(beta2), "tau": float(tau)},
        "rmse_bp": round(rmse_bp, 4),
        "r2": round(r2, 6),
        "fitted": list(fitted),
        "residuals_bp": list((residuals * 100).round(4)),
        "tenors": tenors,
    }


def svensson(tenors: List[str], rates: List[float], tau1_0: float = 1.5, tau2_0: float = 5.0) -> Dict:
    """Svensson (NSS) 拟合"""
    t = _to_days(tenors)
    y = np.array(rates, dtype=float)

    ns_res = nelson_siegel(tenors, rates, tau0=tau1_0)
    x0 = [ns_res["params"]["beta0"], ns_res["params"]["beta1"], ns_res["params"]["beta2"], 0.0, tau1_0, tau2_0]

    res = minimize(_loss, x0, args=(_nss_predict, t, y), method="Nelder-Mead", options={"xatol": 1e-8, "fatol": 1e-10})
    beta0, beta1, beta2, beta3, tau1, tau2 = res.x

    fitted = _nss_predict(res.x, t)
    residuals = y - fitted
    rmse_bp = float(np.sqrt(np.mean(residuals ** 2)) * 100)
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "model": "svensson",
        "params": {
            "beta0": float(beta0), "beta1": float(beta1), "beta2": float(beta2),
            "beta3": float(beta3), "tau1": float(tau1), "tau2": float(tau2),
        },
        "rmse_bp": round(rmse_bp, 4),
        "r2": round(r2, 6),
        "fitted": list(fitted),
        "residuals_bp": list((residuals * 100).round(4)),
        "tenors": tenors,
    }


def fit_model(model_code: str, tenors: List[str], rates: List[float], params: Optional[Dict] = None) -> Dict:
    """统一拟合入口"""
    params = params or {}
    if model_code == "nelson_siegel":
        return nelson_siegel(tenors, rates, tau0=params.get("tau", 1.5))
    elif model_code == "svensson":
        return svensson(tenors, rates, tau1_0=params.get("tau1", 1.5), tau2_0=params.get("tau2", 5.0))
    else:
        raise ValueError(f"unsupported model: {model_code}")