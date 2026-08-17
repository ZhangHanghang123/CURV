"""CURV ORM 模型统一导出"""
from .system import (
    SysUser,
    SysRole,
    SysUserRole,
    SysLlmConfig,
    SysAuditLog,
)
from .dict import SysDictType, SysDictData
from .curve import (
    # 字典（硬编码 fallback）
    CurvTenorStandard,
    CurvRateTypeDict,
    CurvDayCountDict,
    CurvCompoundDict,
    CurvPluginModel,
    # L1
    CurvDataSource,
    CurvCollectionTask,
    CurvCollectionLog,
    # L2
    CurvCurveDefinition,
    CurvRateData,
    CurvCurveVersion,
    CurvDerivedCurve,
    CurvLineage,
    CurvValidationRule,
    # 曲线点定义
    CurvCurvePoint,
    # L3
    CurvFittingParam,
    CurvKeyTenor,
    # L4
    CurvShapeMetric,
    CurvScenario,
    CurvScenarioResult,
    CurvBacktestResult,
    CurvSmartDialogue,
    # L5
    CurvFtpSpreadRule,
    CurvRegulatoryReport,
)

__all__ = [
    # 系统
    "SysUser", "SysRole", "SysUserRole", "SysLlmConfig", "SysAuditLog",
    "SysDictType", "SysDictData",
    # 字典 fallback
    "CurvTenorStandard", "CurvRateTypeDict", "CurvDayCountDict", "CurvCompoundDict", "CurvPluginModel",
    # L1
    "CurvDataSource", "CurvCollectionTask", "CurvCollectionLog",
    # L2
    "CurvCurveDefinition", "CurvRateData", "CurvCurveVersion",
    "CurvDerivedCurve", "CurvLineage", "CurvValidationRule",
    "CurvCurvePoint",
    # L3
    "CurvFittingParam", "CurvKeyTenor",
    # L4
    "CurvShapeMetric", "CurvScenario", "CurvScenarioResult",
    "CurvBacktestResult", "CurvSmartDialogue",
    # L5
    "CurvFtpSpreadRule", "CurvRegulatoryReport",
]