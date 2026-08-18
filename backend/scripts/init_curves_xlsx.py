"""根据 xlsx 曲线清单重新初始化 CURV 数据库

数据源：C:/银行经营/CURV/曲线清单.xlsx
执行：
    cd /c/银行经营/CURV/backend
    /path/to/venv/bin/python3 -m scripts.init_curves_xlsx
"""
import os
import sys
import openpyxl
from datetime import datetime

# 添加 backend 到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings


# ============== 期限集模板 ==============
TENOR_SETS = {
    # 中债登全系（利率债/信用债，标准期限）
    "cnb": ["3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"],
    # 中债中短期票据（短融/中票，更短期限为主）
    "cnb_short": ["1M", "3M", "6M", "9M", "1Y", "2Y", "3Y"],
    # 中债地方政府债（标准）
    "cnb_local": ["1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "15Y", "20Y", "30Y"],
    # 货币市场（短期为主）
    "money_market": ["ON", "7D", "14D", "1M", "3M", "6M", "9M", "1Y"],
    # LPR（单点）
    "lpr": ["1Y", "5Y"],
    # CFETS 利率互换（标准互换期限）
    "swap": ["6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y"],
    # 境外外币曲线
    "fx": ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "30Y"],
    # 派生（利差）
    "derived": ["1Y", "2Y", "3Y", "5Y", "10Y"],
}


# ============== 25 条曲线定义（基于 xlsx 重新设计）==============
# 字段：code, name, category, currency, tenor_set, description, source, rate_type, compound, day_count
CURVE_DEFINITIONS = [
    # ============== 国内人民币-中债登 (6条) ==============
    {
        "code": "cnb_treasury_yield",
        "name": "中债国债收益率曲线",
        "category": "base", "currency": "CNY",
        "tenor_set": "cnb",
        "rate_type_code": "yield", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "中债登发布的国家债券收益率曲线，无风险基准、IRRBB-EVE 折现、估值、FTP",
        "source": "中债登（中国债券信息网）",
        "display_unit": "percent",
    },
    {
        "code": "cnb_policy_fin",
        "name": "中债政策性金融债收益率曲线",
        "category": "credit", "currency": "CNY",
        "tenor_set": "cnb",
        "rate_type_code": "yield", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "国开/进出口/农发行等政策性金融债收益率曲线",
        "source": "中债登（中国债券信息网）",
        "display_unit": "percent",
    },
    {
        "code": "cnb_local_gov",
        "name": "中债地方政府债收益率曲线",
        "category": "base", "currency": "CNY",
        "tenor_set": "cnb_local",
        "rate_type_code": "yield", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "地方政府债收益率曲线，地方债估值、利差计算",
        "source": "中债登（中国债券信息网）",
        "display_unit": "percent",
    },
    {
        "code": "cnb_commercial_bank",
        "name": "中债商业银行普通债收益率曲线",
        "category": "credit", "currency": "CNY",
        "tenor_set": "cnb",
        "rate_type_code": "yield", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "商业银行普通金融债（AAA/AA+），金融债信用估值",
        "source": "中债登（中国债券信息网）",
        "display_unit": "percent",
    },
    {
        "code": "cnb_corp_aaa",
        "name": "中债企业债 AAA 收益率曲线",
        "category": "credit", "currency": "CNY",
        "tenor_set": "cnb",
        "rate_type_code": "yield", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "企业债 AAA 评级收益率曲线",
        "source": "中债登（中国债券信息网）",
        "display_unit": "percent",
    },
    {
        "code": "cnb_corp_aa",
        "name": "中债企业债 AA+ 收益率曲线",
        "category": "credit", "currency": "CNY",
        "tenor_set": "cnb",
        "rate_type_code": "yield", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "企业债 AA+ 评级收益率曲线",
        "source": "中债登（中国债券信息网）",
        "display_unit": "percent",
    },
    {
        "code": "cnb_short_term_note",
        "name": "中债中短期票据收益率曲线",
        "category": "credit", "currency": "CNY",
        "tenor_set": "cnb_short",
        "rate_type_code": "yield", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "中短期票据（含 AAA/AA 评级），短融、中票信用债估值",
        "source": "中债登（中国债券信息网）",
        "display_unit": "percent",
    },

    # ============== 国内人民币-CFETS 货币网 (5条) ==============
    {
        "code": "shibor_curve",
        "name": "Shibor 收益率曲线",
        "category": "money_market", "currency": "CNY",
        "tenor_set": "money_market",
        "rate_type_code": "yield", "compound_code": "simple", "day_count_code": "ACT/360",
        "description": "Shibor(O/N~1Y) 银行间同业拆借利率",
        "source": "全国银行间同业拆借中心 (shibor.net.cn)",
        "display_unit": "percent",
    },
    {
        "code": "repo_7d",
        "name": "银行间质押式回购利率曲线",
        "category": "money_market", "currency": "CNY",
        "tenor_set": "money_market",
        "rate_type_code": "yield", "compound_code": "simple", "day_count_code": "ACT/360",
        "description": "FR001/FR007、FDR001/FDR007，OIS 曲线原始输入",
        "source": "中国货币网 (CFETS)",
        "display_unit": "percent",
    },
    {
        "code": "ncd_curve",
        "name": "同业存单收益率曲线",
        "category": "money_market", "currency": "CNY",
        "tenor_set": "money_market",
        "rate_type_code": "yield", "compound_code": "simple", "day_count_code": "ACT/360",
        "description": "同业存单收益率曲线（交易中心版），NCD 二级市场交易基准",
        "source": "中国货币网 (CFETS)",
        "display_unit": "percent",
    },
    {
        "code": "cfets_swap_fr007",
        "name": "FR007 利率互换收盘曲线",
        "category": "swap", "currency": "CNY",
        "tenor_set": "swap",
        "rate_type_code": "swap_rate", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "FR007 利率互换收盘/定盘曲线，OIS 基准、EVE 折现、利率互换定价",
        "source": "中国货币网 (CFETS)",
        "display_unit": "percent",
    },
    {
        "code": "cfets_swap_fdr007",
        "name": "FDR007 利率互换曲线",
        "category": "swap", "currency": "CNY",
        "tenor_set": "swap",
        "rate_type_code": "swap_rate", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "FDR007 (DR007) 利率互换曲线，存款类机构回购 OIS 曲线",
        "source": "中国货币网 (CFETS)",
        "display_unit": "percent",
    },
    {
        "code": "cfets_swap_shibor3m",
        "name": "Shibor-3M 利率互换曲线",
        "category": "swap", "currency": "CNY",
        "tenor_set": "swap",
        "rate_type_code": "swap_rate", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "Shibor-3M 利率互换曲线，挂钩 Shibor3M 利率互换定价",
        "source": "中国货币网 (CFETS)",
        "display_unit": "percent",
    },
    {
        "code": "cfets_swap_lpr",
        "name": "LPR 利率互换曲线",
        "category": "swap", "currency": "CNY",
        "tenor_set": "swap",
        "rate_type_code": "swap_rate", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "LPR1Y/LPR5Y 利率互换曲线，信贷定价、LPR 互换基准",
        "source": "中国货币网 (CFETS)",
        "display_unit": "percent",
    },

    # ============== LPR（单点） ==============
    {
        "code": "lpr_1y",
        "name": "贷款市场报价利率(LPR)",
        "category": "policy", "currency": "CNY",
        "tenor_set": "lpr",
        "rate_type_code": "policy_rate", "compound_code": "simple", "day_count_code": "ACT/360",
        "description": "LPR-1Y、LPR-5Y，信贷定价、LPR 互换基准",
        "source": "全国银行间同业拆借中心",
        "display_unit": "percent",
    },

    # ============== 国内人民币-上清所 ==============
    {
        "code": "shch_short_term",
        "name": "上清所短融/中期票据收益率曲线",
        "category": "credit", "currency": "CNY",
        "tenor_set": "cnb_short",
        "rate_type_code": "yield", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "上海清算所短融/中期票据收益率曲线，信用债估值补充参考",
        "source": "上海清算所",
        "display_unit": "percent",
    },

    # ============== 境外外币曲线 (6条) ==============
    {
        "code": "sofr_usd",
        "name": "SOFR OIS 收益率曲线（美元）",
        "category": "fx", "currency": "USD",
        "tenor_set": "fx",
        "rate_type_code": "ois_rate", "compound_code": "compound", "day_count_code": "ACT/360",
        "description": "美元 SOFR OIS 曲线，美元账簿折现、衍生品定价",
        "source": "纽约联储、ICE",
        "display_unit": "percent",
    },
    {
        "code": "estr_eur",
        "name": "€STR OIS 收益率曲线（欧元）",
        "category": "fx", "currency": "EUR",
        "tenor_set": "fx",
        "rate_type_code": "ois_rate", "compound_code": "compound", "day_count_code": "ACT/360",
        "description": "欧元 €STR OIS 曲线，欧元账簿折现、衍生品定价",
        "source": "欧洲央行、ICE",
        "display_unit": "percent",
    },
    {
        "code": "sonia_gbp",
        "name": "SONIA OIS 收益率曲线（英镑）",
        "category": "fx", "currency": "GBP",
        "tenor_set": "fx",
        "rate_type_code": "ois_rate", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "英镑 SONIA OIS 曲线，英镑账簿折现、衍生品定价",
        "source": "英格兰银行、ICE",
        "display_unit": "percent",
    },
    {
        "code": "saron_chf",
        "name": "SARON 收益率曲线（瑞士法郎）",
        "category": "fx", "currency": "CHF",
        "tenor_set": "fx",
        "rate_type_code": "ois_rate", "compound_code": "compound", "day_count_code": "ACT/360",
        "description": "瑞士法郎 SARON 曲线，瑞郎业务定价计量",
        "source": "瑞士 SIX 交易所",
        "display_unit": "percent",
    },
    {
        "code": "tonar_jpy",
        "name": "TONAR 收益率曲线（日元）",
        "category": "fx", "currency": "JPY",
        "tenor_set": "fx",
        "rate_type_code": "ois_rate", "compound_code": "compound", "day_count_code": "ACT/360",
        "description": "日元 TONAR 曲线，日元业务定价计量",
        "source": "日本央行",
        "display_unit": "percent",
    },
    {
        "code": "sora_sgd",
        "name": "SORA 收益率曲线（新元）",
        "category": "fx", "currency": "SGD",
        "tenor_set": "fx",
        "rate_type_code": "ois_rate", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "新加坡元 SORA 曲线，新元业务定价计量",
        "source": "新加坡 MAS",
        "display_unit": "percent",
    },

    # ============== 派生曲线 (3条) ==============
    {
        "code": "riskfree_full",
        "name": "无风险收益率曲线（合成）",
        "category": "derived", "currency": "CNY",
        "tenor_set": "cnb",
        "rate_type_code": "synthetic", "compound_code": "compound", "day_count_code": "ACT/365",
        "description": "合成的无风险收益率曲线，用于 FTP 定价底层",
        "source": "合成",
        "display_unit": "percent",
    },
    {
        "code": "credit_spread_aaa",
        "name": "信用利差 AAA",
        "category": "derived", "currency": "CNY",
        "tenor_set": "derived",
        "rate_type_code": "spread", "compound_code": "simple", "day_count_code": "ACT/365",
        "description": "中债 AAA 企业债 - 国债 利差",
        "source": "派生",
        "display_unit": "bp",
    },
    {
        "code": "liquidity_spread",
        "name": "流动性利差",
        "category": "derived", "currency": "CNY",
        "tenor_set": "derived",
        "rate_type_code": "spread", "compound_code": "simple", "day_count_code": "ACT/365",
        "description": "国开 - 国债 流动性利差",
        "source": "派生",
        "display_unit": "bp",
    },
]


def init_xlsx_curves(db_url: str = None):
    """根据 xlsx 清单初始化曲线定义"""
    db_url = db_url or settings.DATABASE_URL
    print(f"[INFO] 连接数据库: {db_url}")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    inserted = 0
    updated = 0
    points_created = 0

    try:
        for c in CURVE_DEFINITIONS:
            code = c["code"]
            tenor_set = TENOR_SETS.get(c["tenor_set"], [])

            # UPSERT 曲线定义
            existing = db.execute(
                text("SELECT id FROM curv_curve_definition WHERE code = :code"),
                {"code": code},
            ).fetchone()

            if existing:
                # 更新（保留字段）
                db.execute(
                    text("""
                        UPDATE curv_curve_definition SET
                            name = :name,
                            curve_category = :category,
                            currency = :currency,
                            tenor_set_json = :tenor_set_json,
                            rate_type_code = :rate_type_code,
                            compound_code = :compound_code,
                            day_count_code = :day_count_code,
                            description = :description,
                            source_id = (SELECT id FROM curv_data_source WHERE code = :source LIMIT 1),
                            display_unit = :display_unit,
                            updated_at = NOW()
                        WHERE code = :code
                    """),
                    {
                        "name": c["name"],
                        "category": c["category"],
                        "currency": c["currency"],
                        "tenor_set_json": str(tenor_set).replace("'", '"'),
                        "rate_type_code": c["rate_type_code"],
                        "compound_code": c["compound_code"],
                        "day_count_code": c["day_count_code"],
                        "description": c["description"],
                        "source": c["source"],
                        "display_unit": c["display_unit"],
                        "code": code,
                    },
                )
                updated += 1
            else:
                # 插入
                db.execute(
                    text("""
                        INSERT INTO curv_curve_definition (
                            code, name, curve_category, currency,
                            tenor_set_json, rate_type_code, compound_code, day_count_code,
                            description, source_id, display_unit,
                            interpolation_method, extrapolation_method, point_unit,
                            precision_digits, is_real_time, owner_role,
                            is_enabled, status, is_deleted,
                            created_by, updated_by, created_at, updated_at
                        ) VALUES (
                            :code, :name, :category, :currency,
                            :tenor_set_json, :rate_type_code, :compound_code, :day_count_code,
                            :description, (SELECT id FROM curv_data_source WHERE code = :source LIMIT 1), :display_unit,
                            'pchip', 'flat', :display_unit,
                            4, 0, '',
                            1, 1, 0,
                            'init_script', 'init_script', NOW(), NOW()
                        )
                    """),
                    {
                        "code": code,
                        "name": c["name"],
                        "category": c["category"],
                        "currency": c["currency"],
                        "tenor_set_json": str(tenor_set).replace("'", '"'),
                        "rate_type_code": c["rate_type_code"],
                        "compound_code": c["compound_code"],
                        "day_count_code": c["day_count_code"],
                        "description": c["description"],
                        "source": c["source"],
                        "display_unit": c["display_unit"],
                    },
                )
                inserted += 1

            # 创建/更新曲线点定义（仅在缺失时插入）
            for i, tenor in enumerate(tenor_set):
                existing_pt = db.execute(
                    text("SELECT id FROM curv_curve_point WHERE curve_code = :code AND tenor = :tenor"),
                    {"code": code, "tenor": tenor},
                ).fetchone()

                if not existing_pt:
                    point_unit = "bp" if c["display_unit"] == "bp" else "percent"
                    point_type = "standard"
                    if c["category"] == "policy" or c["category"] == "money_market":
                        point_type = "key"
                    db.execute(
                        text("""
                            INSERT INTO curv_curve_point (
                                curve_code, tenor, point_unit, point_type,
                                sort_order, description,
                                status, is_deleted,
                                created_by, created_at, updated_at
                            ) VALUES (
                                :code, :tenor, :point_unit, :point_type,
                                :sort_order, '',
                                1, 0,
                                'init_script', NOW(), NOW()
                            )
                        """),
                        {
                            "code": code,
                            "tenor": tenor,
                            "point_unit": point_unit,
                            "point_type": point_type,
                            "sort_order": i,
                        },
                    )
                    points_created += 1

        db.commit()
        print(f"\n[SUCCESS] 曲线定义:")
        print(f"  新增: {inserted} 条")
        print(f"  更新: {updated} 条")
        print(f"  期限点新增: {points_created} 个")

        # 统计当前曲线总数
        total = db.execute(text("SELECT COUNT(*) FROM curv_curve_definition WHERE status=1 AND is_deleted=0")).scalar()
        print(f"  数据库当前曲线总数: {total}")

        # 按分类统计
        rows = db.execute(text("""
            SELECT curve_category, COUNT(*) as cnt
            FROM curv_curve_definition WHERE status=1 AND is_deleted=0
            GROUP BY curve_category
        """)).fetchall()
        print(f"\n  按分类分布:")
        for r in rows:
            print(f"    {r.curve_category or 'unknown'}: {r.cnt}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_xlsx_curves()