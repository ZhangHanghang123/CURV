"""平滑算法"""
from typing import List
import numpy as np
import pandas as pd


def moving_average(rates: List[float], window: int = 5) -> List[float]:
    """移动平均"""
    return list(pd.Series(rates).rolling(window=window, min_periods=1).mean().round(6))


def ewma(rates: List[float], halflife: float = 3.0) -> List[float]:
    """指数加权移动平均"""
    return list(pd.Series(rates).ewm(halflife=halflife).mean().round(6))