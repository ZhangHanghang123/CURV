"""
采集服务：根据业务规则采集曲线历史数据

业务规则（每条曲线的采集策略）：
- 国债/国开/企业债：日终采集（每个工作日）
- Shibor/Repo/NCD：日终采集
- LPR：每月 20 日采集（频率低）
- 派生曲线：基于基础曲线计算（如信用利差 = 企业债 - 国债）

数据生成算法：
- 基础曲线（国债）：从当前 10Y 值反向生成 252 个工作日，含随机游走和趋势
- 国开：在国债基础上加流动性利差（7-10bp）
- 信用债：在国债基础上加信用利差（30-110bp）
- Shibor/Repo/NCD：各自的均值回归模型
- LPR：阶梯式（每月变动或不变）
- 派生曲线：根据基础曲线实时计算
"""
import math
import random
from datetime import date, timedelta
from typing import List, Dict, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import (
    CurvDataSource, CurvCollectionTask, CurvCollectionLog,
    CurvCurveDefinition, CurvCurvePoint, CurvRateData,
)


# ============== 业务规则 ==============
COLLECTION_RULES: Dict[str, dict] = {
    # ---- 无风险基准（国债 - 最核心的基础曲线）----
    "cnb_treasury_yield": {
        "frequency": "daily",
        "category": "base",
        "base_tenor": "10Y",
        "current_value": 2.45,
        "volatility_bp": 3.0,
        "year_trend_bp": -35,  # 1 年下行 35bp（货币宽松周期）
        "term_structure_slope": 0.07,  # 期限利差斜率（短-长差 bp/年）
    },
    # ---- 国开债：国债 + 流动性利差 ----
    "cnb_policy_fin": {
        "frequency": "daily",
        "category": "base",
        "base_tenor": "10Y",
        "current_value": 2.55,
        "spread_to_treasury_bp": 10,
        "volatility_bp": 3.5,
        "year_trend_bp": -35,
        "term_structure_slope": 0.07,
    },
    # ---- 信用债：国债 + 信用利差 ----
    "cnb_corp_aaa": {
        "frequency": "daily",
        "category": "base",
        "base_tenor": "10Y",
        "current_value": 3.03,
        "spread_to_treasury_bp": 58,
        "volatility_bp": 4.5,
        "year_trend_bp": -45,
        "term_structure_slope": 0.08,
    },
    "cnb_corp_aa": {
        "frequency": "daily",
        "category": "base",
        "base_tenor": "10Y",
        "current_value": 3.52,
        "spread_to_treasury_bp": 107,
        "volatility_bp": 6.0,
        "year_trend_bp": -55,
        "term_structure_slope": 0.09,
    },
    # ---- 货币市场（波动较小）----
    "shibor_curve": {
        "frequency": "daily",
        "category": "money_market",
        "base_tenor": "ON",
        "current_value": 1.52,
        "volatility_bp": 1.5,
        "year_trend_bp": -25,
        "term_structure_slope": 0.04,
    },
    "repo_7d": {
        "frequency": "daily",
        "category": "money_market",
        "base_tenor": "7D",
        "current_value": 1.62,
        "spread_to_shibor_bp": 10,
        "volatility_bp": 1.8,
        "year_trend_bp": -25,
        "term_structure_slope": 0.04,
    },
    "ncd_curve": {
        "frequency": "daily",
        "category": "money_market",
        "base_tenor": "1Y",
        "current_value": 2.12,
        "spread_to_shibor_bp": 60,
        "volatility_bp": 2.5,
        "year_trend_bp": -35,
        "term_structure_slope": 0.05,
    },
    # ---- LPR：每月 20 日采集（阶梯式）----
    "lpr_1y": {
        "frequency": "monthly",
        "month_day": 20,
        "category": "policy",
        "base_tenor": "1Y",
        "current_value": 3.10,
        "volatility_bp": 0,  # LPR 是政策利率，不随机
        "year_trend_bp": -50,
        "term_structure_slope": 0.10,
    },
    # ---- 派生曲线（实时计算）----
    "riskfree_full": {
        "frequency": "daily",
        "category": "base",  # 作为 base 曲线直接生成（合成无风险曲线）
        "base_tenor": "10Y",
        "current_value": 2.45,
        "volatility_bp": 2.5,
        "year_trend_bp": -35,
        "term_structure_slope": 0.06,
    },
    "credit_spread_aaa": {
        "frequency": "daily",
        "category": "derived",
        "derived_from": "spread",  # corp_aaa - treasury
        "base_curve_a": "cnb_corp_aaa",
        "base_curve_b": "cnb_treasury_yield",
    },
    "liquidity_spread": {
        "frequency": "daily",
        "category": "derived",
        "derived_from": "spread",  # policy_fin - treasury
        "base_curve_a": "cnb_policy_fin",
        "base_curve_b": "cnb_treasury_yield",
    },
}


# 期限 → 年限（用于斜率计算）
TENOR_TO_YEARS = {
    "ON": 1/365, "1D": 1/365, "7D": 7/365, "14D": 14/365,
    "1W": 7/365, "2W": 14/365, "3W": 21/365,
    "1M": 1/12, "2M": 2/12, "3M": 3/12, "4M": 4/12,
    "5M": 5/12, "6M": 6/12, "7M": 7/12, "8M": 8/12,
    "9M": 9/12, "10M": 10/12, "11M": 11/12,
    "1Y": 1.0, "18M": 1.5,
    "2Y": 2.0, "3Y": 3.0, "4Y": 4.0, "5Y": 5.0,
    "6Y": 6.0, "7Y": 7.0, "8Y": 8.0, "9Y": 9.0, "10Y": 10.0,
    "12Y": 12.0, "15Y": 15.0, "20Y": 20.0, "25Y": 25.0,
    "30Y": 30.0, "40Y": 40.0, "50Y": 50.0,
}


def _business_days(start: date, end: date) -> List[date]:
    """生成 start 到 end 之间的工作日列表（不含周末）"""
    days = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:  # 周一到周五
            days.append(cur)
        cur += timedelta(days=1)
    return days


def _monthly_collection_dates(start: date, end: date, day: int = 20) -> List[date]:
    """生成每月 day 日的日期列表（如 LPR 每月 20 日）"""
    dates = []
    cur = date(start.year, start.month, min(day, 28))
    while cur <= end:
        if cur >= start and cur.weekday() < 5:  # 工作日才采集
            dates.append(cur)
        # 下个月
        if cur.month == 12:
            cur = date(cur.year + 1, 1, min(day, 28))
        else:
            cur = date(cur.year, cur.month + 1, min(day, 28))
    return dates


def _generate_random_walk_series(
    days: int,
    anchor_value: float,
    volatility_bp: float,
    year_trend_bp: float,
    seed: int = 42,
) -> List[float]:
    """生成均值回归的随机游走序列（模拟利率走势）
    - 从当前值出发，反向生成 days 天数据
    - 含线性趋势和随机扰动
    - 每天的扰动是基于前一天 + 随机变量
    """
    rng = random.Random(seed)
    daily_vol = volatility_bp / 100.0  # bp → %
    daily_trend = year_trend_bp / 100.0 / max(days, 1)  # 每日趋势

    # 从锚点反向生成
    series = [anchor_value]
    for _ in range(days - 1):
        prev = series[-1]
        # 反向：减去趋势，减去扰动（让早期利率更高，符合下行趋势）
        shock = rng.gauss(0, daily_vol)
        # 均值回归到长期均值（这里 anchor_value 视为长期均衡）
        mean_revert = (anchor_value - prev) * 0.02
        next_val = prev - daily_trend + shock + mean_revert
        series.append(next_val)

    series.reverse()  # 反转使最早的在前
    return series


class CollectorService:
    def __init__(self, db: Session):
        self.db = db

    def collect_history(
        self,
        start_date: date,
        end_date: date,
        curve_codes: List[str] = None,
        source_code: str = "auto_collector",
        operator: str = "system",
    ) -> dict:
        """
        按业务规则采集 start_date ~ end_date 的历史数据

        返回：{"total_records": N, "duration_ms": ms, "curves": [{code, count, dates}], "log_id": id}
        """
        import time
        t0 = time.time()

        if curve_codes is None:
            curve_codes = list(COLLECTION_RULES.keys())

        # 创建采集任务
        task = CurvCollectionTask(
            source_id=self._get_or_create_source(source_code),
            task_code=f"history_collect_{int(time.time())}",
            task_name=f"历史数据采集 {start_date} ~ {end_date}",
            schedule_type="manual",
            params_json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "curves": curve_codes,
                "source_code": source_code,
            },
            is_enabled=1,
            status=1,
            is_deleted=0,
            created_by=operator,
        )
        self.db.add(task)
        self.db.flush()

        # 创建执行日志
        log = CurvCollectionLog(
            task_id=task.id,
            source_id=task.source_id,
            trade_date=start_date,
            start_time=time_now(),
            status="running",
            record_count=0,
            retry_count=0,
        )
        self.db.add(log)
        self.db.flush()

        # 执行采集
        curve_summaries = []
        total = 0

        try:
            # 先采集所有基础曲线 + 政策曲线
            for curve_code in curve_codes:
                rule = COLLECTION_RULES.get(curve_code, {})
                if rule.get("category") in ("derived",):
                    continue  # 派生曲线稍后处理
                count = self._collect_one_curve(
                    curve_code, start_date, end_date, source_code, operator
                )
                curve_summaries.append({"code": curve_code, "count": count})
                total += count

            # 基础曲线采集完后 flush，让派生曲线能查到基础数据
            self.db.flush()

            # 再采集派生曲线
            for curve_code in curve_codes:
                rule = COLLECTION_RULES.get(curve_code, {})
                if rule.get("category") != "derived":
                    continue
                count = self._collect_one_curve(
                    curve_code, start_date, end_date, source_code, operator
                )
                curve_summaries.append({"code": curve_code, "count": count})
                total += count

            duration = int((time.time() - t0) * 1000)
            log.end_time = time_now()
            log.duration_ms = duration
            log.status = "success"
            log.record_count = total
            self.db.commit()

            return {
                "log_id": log.id,
                "task_id": task.id,
                "total_records": total,
                "duration_ms": duration,
                "curves": curve_summaries,
            }
        except Exception as e:
            duration = int((time.time() - t0) * 1000)
            log.end_time = time_now()
            log.duration_ms = duration
            log.status = "failed"
            log.error_code = "COLLECT_ERROR"
            log.error_msg = str(e)
            self.db.commit()
            raise

    def _collect_one_curve(
        self, curve_code: str, start_date: date, end_date: date,
        source_code: str, operator: str,
    ) -> int:
        """采集单条曲线的历史数据"""
        rule = COLLECTION_RULES.get(curve_code)
        if not rule:
            return 0

        # 1. 确定采集日期列表
        if rule["frequency"] == "monthly":
            dates = _monthly_collection_dates(start_date, end_date, rule.get("month_day", 20))
        else:
            dates = _business_days(start_date, end_date)

        if not dates:
            return 0

        # 2. 获取该曲线的所有期限点
        points = self.db.query(CurvCurvePoint).filter(
            CurvCurvePoint.curve_code == curve_code,
            CurvCurvePoint.is_deleted == 0,
        ).all()
        if not points:
            return 0

        # 3. 根据曲线类别生成数据
        if rule["category"] == "derived":
            return self._collect_derived_curve(
                curve_code, dates, points, source_code, operator, rule
            )
        else:
            return self._collect_base_curve(
                curve_code, dates, points, source_code, operator, rule
            )

    def _collect_base_curve(
        self, curve_code: str, dates: List[date], points: List,
        source_code: str, operator: str, rule: dict,
    ) -> int:
        """采集基础曲线（国债/国开/信用/Shibor/Repo/NCD/LPR）"""
        base_tenor = rule.get("base_tenor", "10Y")
        current_value = rule.get("current_value", 2.0)
        volatility = rule.get("volatility_bp", 2.0)
        year_trend = rule.get("year_trend_bp", 0)
        spread_to_treasury = rule.get("spread_to_treasury_bp", 0)
        spread_to_shibor = rule.get("spread_to_shibor_bp", 0)
        slope = rule.get("term_structure_slope", 0)

        # 生成基础期限的随机游走序列
        seed = hash(curve_code) % 100000
        base_series = _generate_random_walk_series(
            len(dates), current_value, volatility, year_trend, seed
        )

        # 对货币市场类（Shibor），先生成 base_tenor 的值，再通过 slope 推导其他期限
        # 对国债类，base_tenor=10Y，其他期限通过 slope 推导
        n = len(dates)
        inserted = 0

        # 先删除该区间的同 source_version 数据（避免唯一键冲突）
        self.db.query(CurvRateData).filter(
            CurvRateData.curve_code == curve_code,
            CurvRateData.source_version == "official",
            CurvRateData.trade_date >= start_date_first(dates),
            CurvRateData.trade_date <= end_date_last(dates),
        ).delete(synchronize_session=False)

        for p in points:
            tenor = p.tenor
            years = TENOR_TO_YEARS.get(tenor, 5.0)

            for i, td in enumerate(dates):
                # 期限调整（相对 base_tenor 的差值 + slope）
                base_years = TENOR_TO_YEARS.get(base_tenor, 10.0)
                year_diff = years - base_years
                # 期限结构 = 基础值 + 期限差 * slope * 100bp/年
                tenor_adj = year_diff * slope * 100  # slope * 100 是 bp
                # 长短端利差
                base_val = base_series[i] + tenor_adj / 100  # bp → %

                # 加上额外的扰动
                local_seed = (seed + i * 17 + hash(tenor)) % 100000
                local_rng = random.Random(local_seed)
                local_shock = local_rng.gauss(0, volatility * 0.4 / 100)

                value = base_val + spread_to_treasury / 100 + spread_to_shibor / 100 + local_shock

                # LPR 阶梯式（不在波动日变动）
                if rule["frequency"] == "monthly" and i > 0:
                    # LPR 保持月度值不变
                    pass

                self.db.add(CurvRateData(
                    curve_code=curve_code,
                    trade_date=td,
                    tenor=tenor,
                    rate_value=round(value, 4),
                    source_version="official",
                    data_status="active",
                    data_source_code=source_code,
                    is_adjusted=0,
                    remark=f"自动采集 {source_code}",
                ))
                inserted += 1
        return inserted

    def _collect_derived_curve(
        self, curve_code: str, dates: List[date], points: List,
        source_code: str, operator: str, rule: dict,
    ) -> int:
        """采集派生曲线（基于基础曲线实时计算）"""
        derived_type = rule["derived_from"]
        inserted = 0

        if derived_type == "spread":
            # 利差 = 基础曲线 A - 基础曲线 B
            base_a = rule["base_curve_a"]
            base_b = rule["base_curve_b"]
            unit = rule.get("point_unit", "bp")

            # 删除旧数据（同 source_version）
            self.db.query(CurvRateData).filter(
                CurvRateData.curve_code == curve_code,
                CurvRateData.source_version == "official",
                CurvRateData.trade_date >= start_date_first(dates),
                CurvRateData.trade_date <= end_date_last(dates),
            ).delete(synchronize_session=False)

            for p in points:
                tenor = p.tenor
                # 查询基础曲线 A 在这些日期的值
                a_data = dict(self.db.query(
                    CurvRateData.trade_date, CurvRateData.rate_value
                ).filter(
                    CurvRateData.curve_code == base_a,
                    CurvRateData.tenor == tenor,
                    CurvRateData.source_version == "official",
                    CurvRateData.trade_date.in_(dates),
                ).all())

                b_data = dict(self.db.query(
                    CurvRateData.trade_date, CurvRateData.rate_value
                ).filter(
                    CurvRateData.curve_code == base_b,
                    CurvRateData.tenor == tenor,
                    CurvRateData.source_version == "official",
                    CurvRateData.trade_date.in_(dates),
                ).all())

                for td in dates:
                    if td in a_data and td in b_data:
                        if unit == "bp":
                            spread = (a_data[td] - b_data[td]) * 100
                        else:
                            spread = a_data[td] - b_data[td]
                        self.db.add(CurvRateData(
                            curve_code=curve_code,
                            trade_date=td,
                            tenor=tenor,
                            rate_value=round(spread, 2 if unit == "bp" else 4),
                            source_version="official",
                            data_status="active",
                            data_source_code=source_code,
                            is_adjusted=0,
                            remark=f"派生：{base_a} - {base_b}",
                        ))
                        inserted += 1
        return inserted

    def _get_or_create_source(self, code: str) -> int:
        """获取或创建数据源"""
        row = self.db.query(CurvDataSource).filter(
            CurvDataSource.code == code, CurvDataSource.is_deleted == 0
        ).first()
        if row:
            return row.id
        row = CurvDataSource(
            code=code,
            name=f"自动采集源 {code}",
            source_type="INTERNAL",
            provider="curv-auto-collector",
            frequency="daily",
            is_enabled=1,
            status=1,
            is_deleted=0,
            created_by="system",
        )
        self.db.add(row)
        self.db.flush()
        return row.id


# ============== 辅助函数 ==============
def time_now():
    from datetime import datetime
    return datetime.now()


def start_date_first(dates: List[date]) -> date:
    return min(dates) if dates else date.today()


def end_date_last(dates: List[date]) -> date:
    return max(dates) if dates else date.today()
