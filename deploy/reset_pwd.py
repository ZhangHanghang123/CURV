"""重置 admin 密码（passlib 版本，与后端一致）"""
import pymysql
from passlib.context import CryptContext

ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')
new_hash = ctx.hash('admin123')
print('new hash len:', len(new_hash))
print('verify:', ctx.verify('admin123', new_hash))

conn = pymysql.connect(host='127.0.0.1', port=3306, user='curv', password='Curv@2026',
                      database='curv_db', charset='utf8mb4', autocommit=True)
cur = conn.cursor()
cur.execute('UPDATE sys_user SET password_hash=%s WHERE username=%s', (new_hash, 'admin'))
print('updated:', cur.rowcount)
conn.close()