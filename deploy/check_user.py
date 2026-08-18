import pymysql
conn = pymysql.connect(host='127.0.0.1', port=3306, user='curv', password='Curv@2026',
                      database='curv_db', charset='utf8mb4')
cur = conn.cursor()
cur.execute('SELECT id, username, LENGTH(password_hash), status, is_deleted FROM sys_user')
for r in cur.fetchall():
    print(r)
print('---columns---')
cur.execute('SHOW COLUMNS FROM sys_user')
for r in cur.fetchall():
    print(r)