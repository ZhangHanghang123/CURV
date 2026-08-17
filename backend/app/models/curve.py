"""CURV 业务 ORM 模型（曲线、利率、版本、拟合、情景、智能对话）"""
from datetime import datetime, date
from sqlalchemy import BigInteger, String, Integer, DateTime, Date, Text, Numeric, SmallInteger, UniqueConstraint, Index
from sqlalchemy.dialects.mysql import JSON, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


# ============== 字典表 ==============

class CurvTenorStandard(Base):
    __tablename__ = "curv_tenor_standard"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenor_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    tenor_name: Mapped[str] = mapped_column(String(32), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[int] = mapped_column(SmallInteger, default=1)


class CurvRateTypeDict(Base):
    __tablename__ = "curv_rate_type_dict"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class CurvDayCountDict(Base):
    __tablename__ = "curv_day_count_dict"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")


class CurvCompoundDict(Base):
    __tablename__ = "curv_compound_dict"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")


class CurvPluginModel(Base):
    __tablename__ = "curv_plugin_model"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    impl_path: Mapped[str] = mapped_column(String(255), nullable=False)
    params_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    is_enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_builtin: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============== L1 数据采集层 ==============

class CurvDataSource(Base):
    __tablename__ = "curv_data_source"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), default="")
    config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    auth_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    field_mapping_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    frequency: Mapped[str] = mapped_column(String(32), default="daily")
    cron_expr: Mapped[str] = mapped_column(String(64), default="")
    is_enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    last_run_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_run_status: Mapped[str] = mapped_column(String(32), default="")
    last_run_msg: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    updated_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CurvCollectionTask(Base):
    __tablename__ = "curv_collection_task"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    task_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    task_name: Mapped[str] = mapped_column(String(128), nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(32), default="cron")
    cron_expr: Mapped[str] = mapped_column(String(64), default="")
    params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    retry_policy_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    alert_threshold: Mapped[int] = mapped_column(Integer, default=3)
    is_enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    updated_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CurvCollectionLog(Base):
    __tablename__ = "curv_collection_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str] = mapped_column(String(64), default="")
    error_msg: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# ============== L2 数据管理层 ==============

class CurvCurveDefinition(Base):
    __tablename__ = "curv_curve_definition"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    curve_type: Mapped[str] = mapped_column(String(32), default="base")
    curve_category: Mapped[str] = mapped_column(String(32), default="base")
    category: Mapped[str] = mapped_column(String(64), default="")
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    rate_type_code: Mapped[str] = mapped_column(String(32), default="")
    compound_code: Mapped[str] = mapped_column(String(32), default="")
    compounding_method: Mapped[str] = mapped_column(String(32), default="compound")
    day_count_code: Mapped[str] = mapped_column(String(32), default="")
    day_count_method: Mapped[str] = mapped_column(String(32), default="ACT/365")
    interpolation_method: Mapped[str] = mapped_column(String(32), default="pchip")
    extrapolation_method: Mapped[str] = mapped_column(String(32), default="flat")
    display_unit: Mapped[str] = mapped_column(String(16), default="percent")
    point_unit: Mapped[str] = mapped_column(String(16), default="percent")
    precision_digits: Mapped[int] = mapped_column(Integer, default=4)
    is_real_time: Mapped[int] = mapped_column(SmallInteger, default=0)
    tenor_set_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_mapping_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    owner_role: Mapped[str] = mapped_column(String(64), default="")
    is_enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    updated_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CurvRateData(Base):
    """核心事实表：利率数据"""
    __tablename__ = "curv_rate_data"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    curve_code: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    tenor: Mapped[str] = mapped_column(String(16), nullable=False)
    rate_value: Mapped[float] = mapped_column(DECIMAL(12, 6), nullable=False)
    source_version: Mapped[str] = mapped_column(String(32), nullable=False, default="official")
    collection_log_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    data_status: Mapped[str] = mapped_column(String(16), default="active")
    is_adjusted: Mapped[int] = mapped_column(SmallInteger, default=0)
    adjust_reason: Mapped[str] = mapped_column(String(500), default="")
    adjusted_by: Mapped[str] = mapped_column(String(64), default="")
    adjusted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_source_code: Mapped[str] = mapped_column(String(64), default="")
    remark: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("curve_code", "trade_date", "tenor", "source_version", name="uk_curve_date_tenor_ver"),
        Index("idx_curve_date", "curve_code", "trade_date"),
        Index("idx_date", "trade_date"),
        Index("idx_curve_tenor_date", "curve_code", "tenor", "trade_date"),
    )


class CurvCurveVersion(Base):
    __tablename__ = "curv_curve_version"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    curve_code: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    version_no: Mapped[str] = mapped_column(String(32), nullable=False)
    version_status: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_version_no: Mapped[str] = mapped_column(String(32), default="")
    operation_type: Mapped[str] = mapped_column(String(32), default="")
    operation_params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    operation_reason: Mapped[str] = mapped_column(String(500), default="")
    operator: Mapped[str] = mapped_column(String(64), default="")
    is_locked: Mapped[int] = mapped_column(SmallInteger, default=0)
    effective_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("curve_code", "trade_date", "version_no", name="uk_curve_date_ver"),
    )


class CurvDerivedCurve(Base):
    __tablename__ = "curv_derived_curve"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    curve_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    base_curve_codes_json: Mapped[list] = mapped_column(JSON, nullable=False)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    formula_type: Mapped[str] = mapped_column(String(32), default="simple")
    auto_update: Mapped[int] = mapped_column(SmallInteger, default=1)
    description: Mapped[str] = mapped_column(String(500), default="")
    is_enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    updated_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CurvLineage(Base):
    __tablename__ = "curv_lineage"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    data_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    data_table: Mapped[str] = mapped_column(String(64), default="curv_rate_data")
    curve_code: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    tenor: Mapped[str] = mapped_column(String(16), nullable=False)
    source_version: Mapped[str] = mapped_column(String(32), nullable=False)
    upstream_sources_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    operations_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CurvValidationRule(Base):
    __tablename__ = "curv_validation_rule"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    curve_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    rule_type: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="warning")
    is_enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    description: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CurvCurvePoint(Base):
    """曲线点定义：期限点 + 利率值 + 单位 + 类型"""
    __tablename__ = "curv_curve_point"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    curve_code: Mapped[str] = mapped_column(String(64), nullable=False)
    tenor: Mapped[str] = mapped_column(String(16), nullable=False)
    rate_value: Mapped[float | None] = mapped_column(DECIMAL(12, 6), nullable=True)
    point_unit: Mapped[str] = mapped_column(String(16), default="percent", comment="percent/bp/yield/spread")
    point_type: Mapped[str] = mapped_column(String(32), default="standard", comment="standard/key/anchor/manual")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("curve_code", "tenor", "point_type", name="uk_curve_tenor"),
    )


# ============== L3 曲线构建层 ==============

class CurvFittingParam(Base):
    __tablename__ = "curv_fitting_param"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    curve_code: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    version_no: Mapped[str] = mapped_column(String(32), nullable=False)
    model_code: Mapped[str] = mapped_column(String(64), nullable=False)
    params_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    rmse: Mapped[float | None] = mapped_column(DECIMAL(12, 6), nullable=True)
    r2: Mapped[float | None] = mapped_column(DECIMAL(12, 6), nullable=True)
    max_residual_bp: Mapped[float | None] = mapped_column(DECIMAL(12, 6), nullable=True)
    residual_summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fit_status: Mapped[str] = mapped_column(String(32), default="success")
    fit_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operator: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("curve_code", "trade_date", "version_no", "model_code", name="uk_curve_date_ver_model"),
    )


class CurvKeyTenor(Base):
    __tablename__ = "curv_key_tenor"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    curve_code: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    version_no: Mapped[str] = mapped_column(String(32), nullable=False)
    tenor: Mapped[str] = mapped_column(String(16), nullable=False)
    rate_value: Mapped[float] = mapped_column(DECIMAL(12, 6), nullable=False)
    point_type: Mapped[str] = mapped_column(String(32), nullable=False)
    remark: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# ============== L4 分析建模层 ==============

class CurvShapeMetric(Base):
    __tablename__ = "curv_shape_metric"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    curve_code: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[float] = mapped_column(DECIMAL(20, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(16), default="bp")
    params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("curve_code", "trade_date", "metric_code", name="uk_curve_date_metric"),
    )


class CurvScenario(Base):
    __tablename__ = "curv_scenario"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(32), nullable=False)
    shock_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    historical_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_preset: Mapped[int] = mapped_column(SmallInteger, default=0)
    description: Mapped[str] = mapped_column(String(500), default="")
    is_enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CurvScenarioResult(Base):
    __tablename__ = "curv_scenario_result"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    scenario_run_code: Mapped[str] = mapped_column(String(64), nullable=False)
    curve_code: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    asset_liability_id: Mapped[str] = mapped_column(String(64), default="")
    asset_liability_name: Mapped[str] = mapped_column(String(128), default="")
    base_value: Mapped[float | None] = mapped_column(DECIMAL(20, 4), nullable=True)
    shocked_value: Mapped[float | None] = mapped_column(DECIMAL(20, 4), nullable=True)
    pv_change: Mapped[float | None] = mapped_column(DECIMAL(20, 4), nullable=True)
    pv_change_pct: Mapped[float | None] = mapped_column(DECIMAL(12, 6), nullable=True)
    nii_change: Mapped[float | None] = mapped_column(DECIMAL(20, 4), nullable=True)
    nii_change_pct: Mapped[float | None] = mapped_column(DECIMAL(12, 6), nullable=True)
    eve_change: Mapped[float | None] = mapped_column(DECIMAL(20, 4), nullable=True)
    eve_change_pct: Mapped[float | None] = mapped_column(DECIMAL(12, 6), nullable=True)
    krd_vector_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    run_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CurvBacktestResult(Base):
    __tablename__ = "curv_backtest_result"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    backtest_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    test_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_curve: Mapped[str] = mapped_column(String(64), nullable=False)
    model_code: Mapped[str] = mapped_column(String(64), default="")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sample_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    conclusion: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CurvSmartDialogue(Base):
    __tablename__ = "curv_smart_dialogue"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), default="")
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    query: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    agent_trace_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    refs_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    llm_config_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# ============== L5 业务应用层 ==============

class CurvFtpSpreadRule(Base):
    __tablename__ = "curv_ftp_spread_rule"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    product_type: Mapped[str] = mapped_column(String(32), nullable=False)
    product_subtype: Mapped[str] = mapped_column(String(64), default="")
    tenor_min: Mapped[str] = mapped_column(String(16), default="")
    tenor_max: Mapped[str] = mapped_column(String(16), default="")
    base_curve_code: Mapped[str] = mapped_column(String(64), nullable=False)
    spread_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    is_enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CurvRegulatoryReport(Base):
    __tablename__ = "curv_regulatory_report"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), default="")
    file_format: Mapped[str] = mapped_column(String(16), default="xlsx")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    operator: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)