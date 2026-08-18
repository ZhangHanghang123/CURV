"""补全 curv_curve_definition 缺失字段"""
import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='curv', password='Curv@2026',
                      database='curv_db', charset='utf8mb4', autocommit=True)
cur = conn.cursor()

ADDITIONS = [
    "ALTER TABLE curv_curve_definition ADD COLUMN curve_category varchar(32) DEFAULT 'base'",
    "ALTER TABLE curv_curve_definition ADD COLUMN interpolation_method varchar(32) DEFAULT 'pchip'",
    "ALTER TABLE curv_curve_definition ADD COLUMN extrapolation_method varchar(32) DEFAULT 'flat'",
    "ALTER TABLE curv_curve_definition ADD COLUMN day_count_method varchar(32) DEFAULT 'ACT/365'",
    "ALTER TABLE curv_curve_definition ADD COLUMN compounding_method varchar(32) DEFAULT 'compound'",
    "ALTER TABLE curv_curve_definition ADD COLUMN display_unit varchar(16) DEFAULT 'percent'",
    "ALTER TABLE curv_curve_definition ADD COLUMN point_unit varchar(16) DEFAULT 'percent'",
    "ALTER TABLE curv_curve_definition ADD COLUMN precision_digits int DEFAULT 4",
    "ALTER TABLE curv_curve_definition ADD COLUMN is_real_time tinyint DEFAULT 0",
]
cur.execute('SHOW COLUMNS FROM curv_curve_definition')
existing = {r[0] for r in cur.fetchall()}
for sql in ADDITIONS:
    col = sql.split('COLUMN ')[1].split(' ')[0]
    if col in existing:
        print(f'{col} 已存在')
        continue
    try:
        cur.execute(sql)
        print(f'+ {col}')
    except Exception as e:
        print(f'{col}: {e}')
conn.close()