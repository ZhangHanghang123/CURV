"""CURV 完整初始化：建缺失表 + 字典种子 + 11 曲线 + 点定义 + 当日利率数据"""
import pymysql
from datetime import date
import json

DB = dict(host='127.0.0.1', port=3306, user='almd', password='Almd@2026',
          database='curv_db', charset='utf8mb4', autocommit=True)
conn = pymysql.connect(**DB)
cur = conn.cursor()

def exec_sql(sql):
    cur.execute(sql)
def has_table(name):
    cur.execute(f'SHOW TABLES LIKE %s', (name,))
    return bool(cur.fetchone())

def has_column(t, c):
    cur.execute(f'SHOW COLUMNS FROM `{t}` LIKE %s', (c,))
    return bool(cur.fetchone())

def has_dict_type(code):
    cur.execute('SELECT id FROM sys_dict_type WHERE dict_code=%s', (code,))
    return cur.fetchone() is not None

def get_dict_type_id(code, name='', desc=''):
    cur.execute('SELECT id FROM sys_dict_type WHERE dict_code=%s', (code,))
    r = cur.fetchone()
    if r: return r[0]
    cur.execute('INSERT INTO sys_dict_type (dict_code, dict_name, description) VALUES (%s,%s,%s)', (code, name, desc))
    return cur.lastrowid

def add_dict_data(tid, key, label, value='', sort=0, list_class=''):
    cur.execute('SELECT id FROM sys_dict_data WHERE dict_type_id=%s AND dict_key=%s', (tid, key))
    if cur.fetchone(): return
    cur.execute('INSERT INTO sys_dict_data (dict_type_id, dict_label, dict_value, dict_key, sort_order, list_class) VALUES (%s,%s,%s,%s,%s,%s)',
                (tid, label, value or key, key, sort, list_class))

print('=== 1. 建缺失表 ===')

# curv_curve_point
if not has_table('curv_curve_point'):
    cur.execute('''
        CREATE TABLE curv_curve_point (
          id bigint NOT NULL AUTO_INCREMENT,
          curve_code varchar(64) NOT NULL,
          tenor varchar(16) NOT NULL,
          rate_value decimal(12,6) DEFAULT NULL,
          point_unit varchar(16) DEFAULT 'percent',
          point_type varchar(32) DEFAULT 'standard',
          sort_order int NOT NULL DEFAULT 0,
          description varchar(255) DEFAULT '',
          status tinyint NOT NULL DEFAULT 1,
          is_deleted tinyint NOT NULL DEFAULT 0,
          created_by varchar(64) DEFAULT '',
          created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uk_curve_tenor (curve_code, tenor, point_type),
          KEY idx_curve_code (curve_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='曲线点定义'
    ''')
    print('  + curv_curve_point')

# sys_dict_type / sys_dict_data
if not has_table('sys_dict_type'):
    cur.execute('''
        CREATE TABLE sys_dict_type (
          id bigint NOT NULL AUTO_INCREMENT,
          dict_name varchar(128) NOT NULL,
          dict_code varchar(64) NOT NULL,
          description varchar(256) DEFAULT '',
          sort_order int NOT NULL DEFAULT 0,
          status tinyint NOT NULL DEFAULT 1,
          is_deleted tinyint NOT NULL DEFAULT 0,
          created_by bigint DEFAULT NULL,
          updated_by bigint DEFAULT NULL,
          created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id), UNIQUE KEY uk_dict_code (dict_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
if not has_table('sys_dict_data'):
    cur.execute('''
        CREATE TABLE sys_dict_data (
          id bigint NOT NULL AUTO_INCREMENT,
          dict_type_id bigint NOT NULL,
          dict_label varchar(128) NOT NULL,
          dict_value varchar(128) NOT NULL,
          dict_key name varchar(64) NOT NULL,
          css_class varchar(64) DEFAULT '',
          list_class varchar(64) DEFAULT '',
          is_default tinyint NOT NULL DEFAULT 0,
          description varchar(255) DEFAULT '',
          sort_order int NOT NULL DEFAULT 0,
          status tinyint NOT NULL DEFAULT 1,
          is_deleted tinyint NOT NULL DEFAULT 0,
          created_by bigint DEFAULT NULL,
          updated_by bigint DEFAULT NULL,
          created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uk_dict_type_key (dict_type_id, dict_key),
          KEY idx_dict_type (dict_type_id),
          CONSTRAINT fk_dict_type FOREIGN KEY (dict_type_id) REFERENCES sys_dict_type(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
print('  + sys_dict_type / sys_dict_data')

# curv_collection_log / task
for name, sql in [
    ('curv_collection_log', '''CREATE TABLE curv_collection_log (
        id bigint NOT NULL AUTO_INCREMENT, task_id bigint, data_source_code varchar(64),
        trade_date date, status varchar(16) DEFAULT 'pending', record_count int DEFAULT 0,
        duration_ms int DEFAULT 0, error_code varchar(32) DEFAULT '', error_msg text,
        start_time datetime, end_time datetime, created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id), KEY idx_status (status), KEY idx_trade_date (trade_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采集日志' '''),
    ('curv_collection_task', '''CREATE TABLE curv_collection_task (
        id bigint NOT NULL AUTO_INCREMENT, task_code varchar(64), task_name varchar(128),
        curve_codes text, start_date date, end_date date, frequency varchar(16),
        status varchar(16) DEFAULT 'pending', operator varchar(64) DEFAULT '',
        last_run_at datetime, created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id), UNIQUE KEY uk_task_code (task_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采集任务' '''),
]:
    if not has_table(name):
        cur.execute(sql)
        print(f'  + {name}')

print()
print('=== 2. 字典种子数据（14 类字典） ===')
DICTS = {
    'curve_type': ('曲线类型', [('base','基础曲线'),('derived','派生曲线'),('manual','手工录入')]),
    'curve_category': ('曲线大类', [('risk_free','无风险'),('credit','信用'),('money_market','货币市场'),('policy','政策'),('derived','派生')]),
    'rate_type': ('利率类型', [('spot','即期'),('forward','远期'),('yield_to_maturity','到期收益率'),('par_yield','平价收益率'),('spread','利差')]),
    'day_count': ('计息基础', [('ACT/365','实际/365'),('ACT/360','实际/360'),('30/360','30/360'),('ACT/ACT','实际/实际')]),
    'compounding': ('复利方式', [('simple','单利'),('compound','复利'),('continuous','连续复利')]),
    'interpolation_method': ('插值方法', [('linear','线性插值'),('log_linear','对数线性'),('cubic_spline','三次样条'),('pchip','PCHIP'),('nelson_siegel','Nelson-Siegel')]),
    'extrapolation_method': ('外推方法', [('flat','平坦外推'),('linear','线性外推'),('log_linear','对数线性外推')]),
    'point_unit': ('利率单位', [('percent','百分比 (%)'),('bp','基点 (bp)')]),
    'scenario_type': ('情景类型', [('parallel','平行冲击'),('steepener','陡峭化'),('flattener','平坦化'),('historical','历史重演'),('custom','自定义')]),
    'source_type': ('数据源类型', [('API','API接口'),('FILE','文件导入'),('MANUAL','手工录入')]),
    'curve_point_type': ('曲线点类型', [('standard','标准期限'),('key','关键期限'),('anchor','锚点'),('inflection','拐点'),('manual','手工调整')]),
    'model_type': ('拟合模型', [('nelson_siegel','Nelson-Siegel'),('svensson','Svensson(NSS)'),('cubic_spline','三次样条'),('pchip','PCHIP'),('linear','线性'),('log_linear','对数线性')]),
    'validation_rule_type': ('校验规则', [('not_null','非空'),('range','范围'),('monotonicity','单调性'),('reconciliation','对账'),('anomaly','异常检测')]),
    'severity': ('严重程度', [('info','提示'),('warning','警告'),('error','错误'),('critical','严重')]),
}
for code, (name, items) in DICTS.items():
    tid = get_dict_type_id(code, name)
    for i, (k, lbl) in enumerate(items):
        add_dict_data(tid, k, lbl, sort=i)
print(f'  已初始化 {len(DICTS)} 类字典')

# 给 sys_dict_data 加 description 字段
cur.execute('SHOW COLUMNS FROM sys_dict_data')
cols = {r[0] for r in cur.fetchall()}
if 'description' not in cols:
    cur.execute('ALTER TABLE sys_dict_data ADD COLUMN description varchar(255) DEFAULT ""')
    print('  + sys_dict_data.description')

print()
print('=== 3. 11 条曲线定义 ===')
CURVES = [
    ('cnb_treasury_yield','中债国债收益率','base','risk_free','yield_to_maturity','ACT/365','compound','nelson_siegel','flat','percent',
     '中华人民共和国财政部发行的国债二级市场到期收益率，是无风险利率基准',
     ['1M','3M','6M','9M','1Y','2Y','3Y','5Y','7Y','10Y','15Y','20Y','30Y'],
     {'1M':1.45,'3M':1.58,'6M':1.65,'9M':1.72,'1Y':1.77,'2Y':1.85,'3Y':1.95,'5Y':2.15,'7Y':2.32,'10Y':2.45,'15Y':2.62,'20Y':2.72,'30Y':2.78},
     ['3M','1Y','5Y','10Y','30Y']),
    ('cnb_policy_fin','中债国开债收益率','base','risk_free','yield_to_maturity','ACT/365','compound','nelson_siegel','flat','percent',
     '国家开发银行发行的政策性金融债收益率，反映准政府信用',
     ['1M','3M','6M','9M','1Y','2Y','3Y','5Y','7Y','10Y','15Y','20Y','30Y'],
     {'1M':1.52,'3M':1.65,'6M':1.72,'9M':1.79,'1Y':1.85,'2Y':1.94,'3Y':2.04,'5Y':2.25,'7Y':2.42,'10Y':2.55,'15Y':2.73,'20Y':2.83,'30Y':2.90},
     ['3M','1Y','5Y','10Y','30Y']),
    ('cnb_corp_aaa','中债企业债AAA','base','credit','yield_to_maturity','ACT/365','compound','cubic_spline','flat','percent',
     '信用等级AAA的企业债二级市场到期收益率',
     ['1Y','2Y','3Y','5Y','7Y','10Y','15Y','20Y','30Y'],
     {'1Y':2.12,'2Y':2.23,'3Y':2.37,'5Y':2.65,'7Y':2.87,'10Y':3.03,'15Y':3.24,'20Y':3.36,'30Y':3.46}, ['1Y','5Y','10Y']),
    ('cnb_corp_aa','中债企业债AA+','base','credit','yield_to_maturity','ACT/365','compound','cubic_spline','flat','percent',
     '信用等级AA+的企业债二级市场到期收益率',
     ['1Y','2Y','3Y','5Y','7Y','10Y','15Y','20Y','30Y'],
     {'1Y':2.45,'2Y':2.58,'3Y':2.75,'5Y':3.05,'7Y':3.32,'10Y':3.52,'15Y':3.78,'20Y':3.92,'30Y':4.05}, ['1Y','5Y','10Y']),
    ('shibor_curve','Shibor','base','money_market','spot','ACT/360','simple','linear','flat','percent',
     '18家商业银行报出的同业拆借利率，反映货币市场基准',
     ['ON','1W','2W','1M','3M','6M','9M','1Y'],
     {'ON':1.52,'1W':1.65,'2W':1.72,'1M':1.78,'3M':1.85,'6M':1.92,'9M':1.98,'1Y':2.05}, ['ON','1W','3M']),
    ('repo_7d','银行间质押式回购','base','money_market','spot','ACT/360','simple','linear','flat','percent',
     '银行间市场质押式回购加权利率',
     ['1D','7D','14D','1M','3M','6M','9M','1Y'],
     {'1D':1.50,'7D':1.62,'14D':1.68,'1M':1.75,'3M':1.82,'6M':1.88,'9M':1.94,'1Y':2.00}, ['1D','7D']),
    ('ncd_curve','同业存单','base','money_market','yield_to_maturity','ACT/360','simple','pchip','flat','percent',
     '商业银行在同业市场发行的可转让存单收益率',
     ['1M','3M','6M','9M','1Y','2Y','3Y','5Y'],
     {'1M':1.82,'3M':1.90,'6M':1.97,'9M':2.05,'1Y':2.12,'2Y':2.28,'3Y':2.45,'5Y':2.62}, ['3M','1Y']),
    ('lpr_1y','贷款市场报价利率(LPR)','manual','policy','par_yield','ACT/360','simple','linear','flat','percent',
     '由全国银行间同业拆借中心公布的贷款基准利率',
     ['1Y','5Y'], {'1Y':3.10,'5Y':3.60}, ['1Y','5Y']),
    ('riskfree_full','无风险收益率曲线(合成)','derived','derived','par_yield','ACT/365','compound','nelson_siegel','flat','percent',
     'SHIBOR(短期)+国债(中长期)合成的完整无风险曲线',
     ['1D','7D','1M','3M','6M','9M','1Y','2Y','3Y','5Y','7Y','10Y','15Y','20Y','30Y'],
     {'1D':1.50,'7D':1.62,'1M':1.72,'3M':1.80,'6M':1.88,'9M':1.95,'1Y':1.77,'2Y':1.85,'3Y':1.95,'5Y':2.15,'7Y':2.32,'10Y':2.45,'15Y':2.62,'20Y':2.72,'30Y':2.78},
     ['1Y','5Y','10Y','30Y']),
    ('credit_spread_aaa','信用利差AAA','derived','derived','spread','ACT/365','simple','pchip','flat','bp',
     'AAA企业债与同期限国债的收益率利差(单位bp)',
     ['1Y','2Y','3Y','5Y','7Y','10Y','15Y','20Y','30Y'],
     {'1Y':35,'2Y':38,'3M':42,'5Y':50,'7Y':55,'10Y':58,'15Y':62,'20Y':64,'30Y':68}, ['1Y','5Y','10Y']),
    ('liquidity_spread','流动性利差','derived','derived','spread','ACT/365','simple','pchip','flat','bp',
     '国开债与同期限国债的收益率利差(单位bp)',
     ['1M','3M','6M','9M','1Y','2Y','3Y','5Y'],
     {'1M':7,'3M':7,'6M':7,'9M':7,'1Y':8,'2Y':9,'3Y':9,'5Y':10}, ['1Y','5Y']),
]

for code, name, ctype, ccat, rtype, day, comp, interp, extrap, unit, desc, tenors, rates, keys in CURVES:
    cur.execute('SELECT id FROM curv_curve_definition WHERE code=%s', (code,))
    if cur.fetchone():
        cur.execute('''UPDATE curv_curve_definition SET name=%s, curve_type=%s, curve_category=%s,
            rate_type_code=%s, day_count_method=%s, compounding_method=%s, interpolation_method=%s,
            extrapolation_method=%s, point_unit=%s, description=%s, tenor_set_json=%s, currency=%s,
            display_unit=%s, category=%s WHERE code=%s''',
            (name, ctype, ccat, rtype, day, comp, interp, extrap, unit, desc, json.dumps(tenors), 'CNY', unit, ccat, code))
    else:
        cur.execute('''INSERT INTO curv_curve_definition (code,name,curve_type,curve_category,rate_type_code,
            day_count_method,compounding_method,interpolation_method,extrapolation_method,display_unit,
            point_unit,precision_digits,description,tenor_set_json,currency,category,is_enabled,status,is_deleted,created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,4,%s,%s,%s,%s,1,1,0,'init')''',
            (code, name, ctype, ccat, rtype, day, comp, interp, extrap, unit, unit, desc, json.dumps(tenors), 'CNY', ccat))
    print(f'  曲线: {code} ({len(tenors)} 个期限)')

# 清空旧点
cur.execute('DELETE FROM curv_curve_point')

# 插入曲线点
total_points = 0
for code, name, ctype, ccat, rtype, day, comp, interp, extrap, unit, desc, tenors, rates, keys in CURVES:
    for idx, t in enumerate(tenors):
        rate = rates.get(t)
        pt = 'key' if t in keys else 'standard'
        cur.execute('INSERT INTO curv_curve_point (curve_code,tenor,rate_value,point_unit,point_type,sort_order,description,status,is_deleted,created_by) VALUES (%s,%s,%s,%s,%s,%s,%s,1,0,%s)',
                    (code, t, rate, unit, pt, idx+1, '', 'init'))
        total_points += 1
print(f'  生成 {total_points} 个曲线点')

print()
print('=== 4. 当日利率数据 ===')
trade_date = date.today().isoformat()
cur.execute("DELETE FROM curv_rate_data WHERE data_source_code='seed'")
ins = 0
for code, name, ctype, ccat, rtype, day, comp, interp, extrap, unit, desc, tenors, rates, keys in CURVES:
    for t in tenors:
        rate = rates.get(t)
        if rate is None: continue
        cur.execute('INSERT INTO curv_rate_data (curve_code,trade_date,tenor,rate_value,source_version,data_status,data_source_code,is_adjusted,remark) VALUES (%s,%s,%s,%s,%s,%s,%s,0,%s) ON DUPLICATE KEY UPDATE rate_value=VALUES(rate_value)',
                    (code, trade_date, t, rate, 'official', 'active', 'seed', ''))
        ins += 1
print(f'  插入 {ins} 行 curv_rate_data (日期 {trade_date})')

print()
print('=== 5. admin 密码重置 ===')
# 重置 admin 密码为 admin123
import bcrypt
new_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
cur.execute('UPDATE sys_user SET password_hash=%s WHERE username=%s', (new_hash, 'admin'))
print(f'  admin 密码已重置')

cur.execute('SELECT COUNT(*) FROM curv_curve_definition'); print(f'\n=== 验证 ===\n  曲线定义: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM curv_curve_point'); print(f'  曲线点: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM curv_rate_data'); print(f'  利率数据: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM sys_dict_type'); print(f'  字典类型: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM sys_dict_data'); print(f'  字典码值: {cur.fetchone()[0]}')
conn.close()