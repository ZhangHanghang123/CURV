"""
CURV 数据库初始化脚本
1. 创建 curv 用户
2. 创建 curv_db 数据库
3. 导入 curv_db.sql 全部表结构 + 种子数据
"""
import pymysql
import re
import sys

# ===== 配置 =====
ROOT_PWD = "root"
DB_USER = "curv"
DB_PWD = "Curv@2026"  # URL 中 @ 需要编码为 %40
DB_NAME = "curv_db"
SQL_FILE = r"C:\银行经营\CURV\curv_db.sql"


def split_sql_statements(sql_text: str):
    """简单分句（按 ; 分割，但忽略字符串内的 ;）"""
    statements = []
    buf = []
    in_string = False
    string_char = None
    in_comment = False
    i = 0
    while i < len(sql_text):
        ch = sql_text[i]
        # 行注释 -- ... \n
        if not in_string and ch == "-" and i + 1 < len(sql_text) and sql_text[i + 1] == "-":
            # 跳到行尾
            while i < len(sql_text) and sql_text[i] != "\n":
                buf.append(sql_text[i])
                i += 1
            continue
        if not in_string and ch == "#":
            while i < len(sql_text) and sql_text[i] != "\n":
                buf.append(sql_text[i])
                i += 1
            continue
        # 块注释 /* ... */
        if not in_string and ch == "/" and i + 1 < len(sql_text) and sql_text[i + 1] == "*":
            while i < len(sql_text):
                buf.append(sql_text[i])
                if sql_text[i] == "*" and i + 1 < len(sql_text) and sql_text[i + 1] == "/":
                    buf.append("/")
                    i += 2
                    break
                i += 1
            continue
        # 字符串
        if not in_string and ch in ("'", '"', "`"):
            in_string = True
            string_char = ch
            buf.append(ch)
            i += 1
            continue
        if in_string:
            if ch == "\\" and i + 1 < len(sql_text):
                buf.append(ch)
                buf.append(sql_text[i + 1])
                i += 2
                continue
            if ch == string_char:
                in_string = False
                string_char = None
            buf.append(ch)
            i += 1
            continue
        # 语句结束
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    # 末尾
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def main():
    print(f"=== CURV 数据库初始化 ===")
    print(f"目标用户: {DB_USER}")
    print(f"目标数据库: {DB_NAME}")

    # 1. 用 root 连接（无数据库）
    conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password=ROOT_PWD, charset="utf8mb4", autocommit=True)
    cur = conn.cursor()
    print(f"\n[1] 已用 root 连接 MySQL 8.4")

    # 2. 删除旧 curv 用户（如果存在）
    cur.execute(f"DROP USER IF EXISTS '{DB_USER}'@'localhost'")
    cur.execute(f"DROP USER IF EXISTS '{DB_USER}'@'127.0.0.1'")
    cur.execute(f"DROP USER IF EXISTS '{DB_USER}'@'%'")
    print(f"[2] 已清理旧的 {DB_USER} 用户")

    # 3. 创建 curv 用户（MySQL 8 默认 caching_sha2_password）
    cur.execute(f"CREATE USER '{DB_USER}'@'localhost' IDENTIFIED BY '{DB_PWD}'")
    cur.execute(f"CREATE USER '{DB_USER}'@'127.0.0.1' IDENTIFIED BY '{DB_PWD}'")
    cur.execute(f"CREATE USER '{DB_USER}'@'%' IDENTIFIED BY '{DB_PWD}'")
    print(f"[3] 已创建 {DB_USER} 用户（密码 {DB_PWD}）")

    # 4. 创建数据库（如果不存在）
    cur.execute(f"DROP DATABASE IF EXISTS `{DB_NAME}`")
    cur.execute(
        f"CREATE DATABASE `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci"
    )
    print(f"[4] 已创建数据库 {DB_NAME}")

    # 5. 授权
    cur.execute(f"GRANT ALL PRIVILEGES ON `{DB_NAME}`.* TO '{DB_USER}'@'localhost'")
    cur.execute(f"GRANT ALL PRIVILEGES ON `{DB_NAME}`.* TO '{DB_USER}'@'127.0.0.1'")
    cur.execute(f"GRANT ALL PRIVILEGES ON `{DB_NAME}`.* TO '{DB_USER}'@'%'")
    cur.execute("FLUSH PRIVILEGES")
    print(f"[5] 已授权 {DB_USER} 对 {DB_NAME} 的全部权限")

    # 6. 切换到 curv_db
    conn.select_db(DB_NAME)

    # 7. 读取并执行 curv_db.sql
    print(f"\n[6] 导入 SQL 文件: {SQL_FILE}")
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_text = f.read()

    statements = split_sql_statements(sql_text)
    print(f"    解析到 {len(statements)} 条 SQL 语句")

    success = 0
    failed = 0
    for idx, stmt in enumerate(statements, 1):
        # 跳过 USE curv_db（已切换）
        if stmt.upper().startswith("USE "):
            continue
        # 跳过 CREATE DATABASE（已建）
        if stmt.upper().startswith("CREATE DATABASE"):
            continue
        try:
            cur.execute(stmt)
            success += 1
        except Exception as e:
            failed += 1
            print(f"    ✗ [{idx}] {stmt[:80]}...")
            print(f"      错误: {e}")

    print(f"\n[7] 执行完成: 成功 {success} / 失败 {failed}")

    # 8. 验证
    cur.execute("SHOW TABLES")
    tables = [r[0] for r in cur.fetchall()]
    print(f"\n[8] 数据库 {DB_NAME} 共 {len(tables)} 张表:")
    for t in tables:
        # 统计行数
        cur.execute(f"SELECT COUNT(*) FROM `{t}`")
        cnt = cur.fetchone()[0]
        print(f"    {t:40s} {cnt:6d} 行")

    # 9. 测试 curv 用户登录
    print(f"\n[9] 验证 {DB_USER} 用户登录...")
    conn2 = pymysql.connect(
        host="127.0.0.1", port=3306, user=DB_USER, password=DB_PWD, database=DB_NAME, charset="utf8mb4"
    )
    with conn2.cursor() as c:
        c.execute("SELECT COUNT(*) FROM curv_rate_data")
        print(f"    ✓ {DB_USER} 登录成功，可访问 curv_rate_data")
    conn2.close()

    conn.close()
    print(f"\n=== 完成 ===")
    print(f"连接串: mysql+pymysql://{DB_USER}:Curv%402026@127.0.0.1:3306/{DB_NAME}?charset=utf8mb4")


if __name__ == "__main__":
    main()