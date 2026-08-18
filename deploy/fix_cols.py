"""补 sys_role 和 sys_user_role 缺失字段"""
import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='curv', password='Curv@2026',
                      database='curv_db', charset='utf8mb4', autocommit=True)
cur = conn.cursor()

ADDITIONS = {
    'sys_role': [
        ('updated_at', 'datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
        ('updated_by', 'BIGINT NULL'),
        ('created_by', 'BIGINT NULL'),
        ('sort_order', 'int DEFAULT 0'),
    ],
    'sys_user_role': [
        ('created_at', 'datetime NOT NULL DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
        ('updated_by', 'BIGINT NULL'),
        ('created_by', 'BIGINT NULL'),
    ],
    'sys_llm_config': [
        ('updated_at', 'datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
    ],
    'sys_audit_log': [
        ('created_at', 'datetime NOT NULL DEFAULT CURRENT_TIMESTAMP'),
    ],
}
for tbl, cols in ADDITIONS.items():
    cur.execute(f'SHOW COLUMNS FROM {tbl}')
    existing = {r[0] for r in cur.fetchall()}
    for col, defn in cols:
        if col in existing:
            continue
        try:
            cur.execute(f'ALTER TABLE `{tbl}` ADD COLUMN `{col}` {defn}')
            print(f'+ {tbl}.{col}')
        except Exception as e:
            print(f'{tbl}.{col}: {e}')
conn.close()