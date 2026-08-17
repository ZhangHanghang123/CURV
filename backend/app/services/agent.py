"""CURVE_CHAT 智能问数服务（简化规则版 + 可选 LLM 扩展）"""
from datetime import date, timedelta
from typing import Dict, Optional, List
import json
import re
import uuid

from sqlalchemy.orm import Session

from ..models import CurvRateData, CurvSmartDialogue, CurvCurveDefinition, SysLlmConfig
from .builder import BuildService
from .analyzer import AnalyzerService
from .scenario import ScenarioService


class CurveChatService:
    """CURV 平台的智能对话入口

    一期实现：基于意图识别 + 规则引擎 + 数据查询（无 LLM 依赖即可工作）
    二期扩展：接入 LangGraph + DeepSeek LLM 实现自然语言生成
    """

    def __init__(self, db: Session):
        self.db = db
        self.builder = BuildService(db)
        self.analyzer = AnalyzerService(db)
        self.scenario = ScenarioService(db)

    def chat(
        self,
        user_query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict:
        """主入口"""
        session_id = session_id or f"S-{uuid.uuid4().hex[:12]}"
        # 1. 意图识别
        intent = self._classify_intent(user_query)
        # 2. 实体抽取
        entities = self._extract_entities(user_query)
        # 3. 执行
        try:
            answer_data = self._execute_intent(intent, entities)
        except Exception as e:
            answer_data = {"text": f"执行出错：{e}", "charts": [], "refs": []}

        # 4. 组装回答
        text = answer_data.get("text", "")
        charts = answer_data.get("charts", [])
        refs = answer_data.get("refs", [])

        # 5. 持久化对话
        try:
            self.db.add(CurvSmartDialogue(
                session_id=session_id,
                user_id=user_id or "",
                role="user",
                query=user_query,
            ))
            self.db.add(CurvSmartDialogue(
                session_id=session_id,
                user_id=user_id or "",
                role="assistant",
                content=text,
                agent_trace_json={"intent": intent, "entities": entities},
                result_json={"charts": charts},
                refs_json=refs,
            ))
            self.db.commit()
        except Exception:
            self.db.rollback()

        return {
            "session_id": session_id,
            "intent": intent,
            "entities": entities,
            "text": text,
            "charts": charts,
            "references": refs,
        }

    def _classify_intent(self, query: str) -> str:
        """简单关键词分类"""
        q = query.lower()
        if any(k in q for k in ["走势", "趋势", "历史", "今年", "去年", "近一年", "近一月"]):
            return "trend"
        if any(k in q for k in ["利差", "spread", "信用利差"]):
            return "spread"
        if any(k in q for k in ["拟合", "nelson", "siegel", "svensson"]):
            return "fit"
        if any(k in q for k in ["情景", "冲击", "上行", "下行", "压力测试", "parallel"]):
            return "scenario"
        if any(k in q for k in ["构建", "拼接", "无风险", "splice"]):
            return "build"
        if any(k in q for k in ["异常", "告警", "质量"]):
            return "validate"
        if any(k in q for k in ["krd", "久期", "敏感度"]):
            return "krd"
        if any(k in q for k in ["当前", "今天", "最新", "多少"]):
            return "current"
        return "chat"

    def _extract_entities(self, query: str) -> Dict:
        """实体抽取：曲线、期限、日期、操作"""
        entities = {"curve_code": None, "tenor": None, "date": None, "shock_bp": None}

        # 曲线识别
        if "国债" in query:
            entities["curve_code"] = "cnb_treasury_yield"
        elif "国开" in query or "政策性金融" in query:
            entities["curve_code"] = "cnb_policy_fin"
        elif "企业债" in query or "aaa" in query.lower():
            entities["curve_code"] = "cnb_corp_aaa"
        elif "shibor" in query.lower():
            entities["curve_code"] = "shibor_curve"
        elif "repo" in query.lower() or "回购" in query:
            entities["curve_code"] = "repo_7d"

        # 期限识别
        for t in ["30Y", "20Y", "15Y", "10Y", "7Y", "5Y", "3Y", "1Y", "9M", "6M", "3M", "1M"]:
            if t.lower() in query.lower():
                entities["tenor"] = t
                break

        # 日期识别
        m = re.search(r"(\d{4})[-/年](\d{1,2})(?:[-/月](\d{1,2}))?", query)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)
            entities["date"] = date(y, mo, min(d, 28))

        # 冲击 bp 识别
        m = re.search(r"([+-]?\d+)\s*bp", query.lower())
        if m:
            entities["shock_bp"] = int(m.group(1))

        return entities

    def _execute_intent(self, intent: str, entities: Dict) -> Dict:
        """执行意图，返回 text/charts/refs"""
        curve_code = entities.get("curve_code") or "cnb_treasury_yield"
        tenor = entities.get("tenor") or "10Y"
        trade_date = entities.get("date") or date.today()

        if intent == "trend":
            start = trade_date - timedelta(days=365)
            res = self.analyzer.get_trend(curve_code, tenor, start, trade_date)
            stats = res.get("stats", {})
            text = (
                f"📈 **{curve_code}** 在 **{tenor}** 期限 "
                f"从 {res['dates'][0] if res['dates'] else '-'} 到 {res['dates'][-1] if res['dates'] else '-'} "
                f"共有 {stats.get('count', 0)} 个交易日。\n\n"
                f"- 均值: **{stats.get('mean', 0):.2f}%**\n"
                f"- 最大值: **{stats.get('max', 0):.2f}%**（{res['dates'][res['rates'].index(stats.get('max'))] if res['rates'] else '-'}）\n"
                f"- 最小值: **{stats.get('min', 0):.2f}%**\n"
                f"- 年化波动率: **{stats.get('annual_volatility', 0):.2f}%**"
            )
            charts = [{"type": "line", "title": f"{tenor} 走势", "data": {"dates": res["dates"], "values": res["rates"]}}]
            refs = [{"title": "基于 curv_rate_data 历史数据"}]
            return {"text": text, "charts": charts, "refs": refs}

        if intent == "spread":
            res = self.analyzer.shape_metrics(curve_code, trade_date)
            metrics = res.get("metrics", {})
            text = "📐 **形态指标：**\n\n"
            for k, v in metrics.items():
                text += f"- {k}: **{v}**\n"
            charts = [{"type": "bar", "title": "形态指标", "data": metrics}]
            return {"text": text, "charts": charts, "refs": []}

        if intent == "fit":
            res = self.builder.fit(curve_code, trade_date, model="nelson_siegel")
            if "error" in res:
                return {"text": f"拟合失败：{res['error']}", "charts": [], "refs": []}
            text = (
                f"⚙️ **Nelson-Siegel 拟合结果**\n\n"
                f"- β₀（水平）: **{res['params']['beta0']:.4f}**\n"
                f"- β₁（斜率）: **{res['params']['beta1']:.4f}**\n"
                f"- β₂（曲率）: **{res['params']['beta2']:.4f}**\n"
                f"- τ: **{res['params']['tau']:.4f}**\n"
                f"- RMSE: **{res['rmse_bp']:.2f}bp**（{'✓ 达标' if res['rmse_bp'] <= 2 else '⚠ 超阈'}）\n"
                f"- R²: **{res['r2']:.4f}**"
            )
            return {"text": text, "charts": [], "refs": []}

        if intent == "scenario":
            bp = entities.get("shock_bp") or 100
            scenarios = self.scenario.list_scenarios()
            sce = next((s for s in scenarios if s["scenario_type"] == "parallel" and s["shock_json"].get("shock_bp") == bp), None)
            if not sce and scenarios:
                sce = scenarios[0]
            if not sce:
                return {"text": "未找到可用情景", "charts": [], "refs": []}
            res = self.scenario.run_scenario(sce["id"], curve_code, trade_date, portfolio_value=10000.0, duration=5.0)
            text = (
                f"🌪️ **情景：{sce['name']}**\n\n"
                f"- 组合原值: **{res['base_value']:.2f} 万**\n"
                f"- 冲击后: **{res['shocked_value']:.2f} 万**\n"
                f"- PV 变化: **{res['pv_change']:.2f} 万** ({res['pv_change_pct']:.2f}%)\n"
                f"- NII 变化: **{res['nii_change']:.2f} 万**\n"
                f"- EVE 变化: **{res['eve_change']:.2f} 万**"
            )
            return {"text": text, "charts": [], "refs": []}

        if intent == "krd":
            res = self.analyzer.krd(curve_code, trade_date, shock_bp=1.0)
            text = (
                f"🎯 **关键利率久期（1bp 冲击）**\n\n"
                f"- 总 DV01: **{res['total_dv01']:.2f} 元**\n"
                f"- 主要暴露期限:"
            )
            for t, v in res["krd_vector"].items():
                if v is not None:
                    text += f"\n  - {t}: KRD={v} 年"
            return {"text": text, "charts": [{"type": "bar", "title": "KRD 向量", "data": res["krd_vector"]}], "refs": []}

        if intent == "current":
            rows = (
                self.db.query(CurvRateData)
                .filter(
                    CurvRateData.curve_code == curve_code,
                    CurvRateData.tenor == tenor,
                    CurvRateData.source_version == "official",
                )
                .order_by(CurvRateData.trade_date.desc())
                .limit(5)
                .all()
            )
            if not rows:
                return {"text": f"未找到 {curve_code} {tenor} 的数据", "charts": [], "refs": []}
            latest = rows[0]
            text = f"📊 **{curve_code}** 在 **{tenor}** 期限最新数据：\n\n"
            text += f"- 最新交易日: **{latest.trade_date}**\n"
            text += f"- 利率: **{float(latest.rate_value):.2f}%**\n"
            text += f"- 版本: **{latest.source_version}**"
            return {"text": text, "charts": [], "refs": []}

        if intent == "validate":
            return {"text": "🔍 数据校验功能开发中，可通过 L4 形态指标查看", "charts": [], "refs": []}

        # 默认对话
        return {
            "text": (
                "🤖 您好！我是 CURV 智能助手。\n\n"
                "可以问我：\n"
                "- 「10年国债近一年走势」\n"
                "- 「信用利差最近如何」\n"
                "- 「今天曲线数据有什么异常」\n"
                "- 「利率上行100bp，EVE变多少」\n"
                "- 「构建一条无风险收益率曲线」\n"
                "- 「拟合10年国债曲线」"
            ),
            "charts": [],
            "refs": [],
        }