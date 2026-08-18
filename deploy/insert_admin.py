"""插入 admin 用户"""
import pymysql
from passlib.context import CryptContext

ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')
hash_pwd = ctx.hash('admin123')

conn = pymysql.connect(host='127.0.0.1', port=3306, user='curv', password='Curv@2026',
                      database='curv_db', charset='utf8mb4', autocommit=True)
cur = conn.cursor()

# 1. 插入 admin 用户
cur.execute('SELECT COUNT(*) FROM sys_user WHERE username=%s', ('admin',))
if cur.fetchone()[0] == 0:
    cur.execute('''INSERT INTO sys_user (username, password_hash, real_name, email, is_admin, status)
                   VALUES (%s, %s, %s, %s, 1, 1)''',
                ('admin', hash_pwd, '系统管理员', 'admin@bank.local'))
    print('+ admin user created')
else:
    cur.execute('UPDATE sys_user SET password_hash=%s WHERE username=%s', (hash_pwd, 'admin'))
    print('~ admin password reset')

# 2. 插入 demo 用户
hash_demo = ctx.hash('demo123')
if not cur.execute('SELECT 1 FROM sys_user WHERE username=%s', ('demo',)):
    cur.execute('''INSERT INTO sys_user (username, password_hash, real_name, is_admin, status)
                   VALUES (%s, %s, %s, 0, 1)''', ('demo', hash_demo, '演示账号'))

# 3. 插入角色
cur.execute('SELECT COUNT(*) FROM sys_role')
if cur.fetchone()[0] == 0:
    cur.execute('INSERT INTO sys_role (role_code, role_name, description) VALUES (%s,%s,%s)',
                ('admin', '系统管理员', '拥有全部权限'))
    cur.execute('INSERT INTO sys_role (role_code, role_name, description) VALUES (%s,%s,%s)',
                ('viewer', '查看者', '只读权限'))
    print('+ 2 roles created')

cur.execute('SELECT id, username, real_name, is_admin, status FROM sys_user')
for r in cur.fetchall():
    print(r)
conn.close()