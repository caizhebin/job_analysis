# -*- coding: utf-8 -*-
"""
03_导入MySQL.py —— 把清洗后的 CSV 导入 MySQL（你电脑上已装好 MySQL Server 8.0 且在运行）

运行前唯一要做的事：把下面 MYSQL_PASSWORD 改成你的 root 密码
（就是当初装 MySQL 时设置的那个；忘了的话告诉我，带你走重置流程）

运行：py 03_导入MySQL.py
产出：MySQL 里的 jobs 库、job_postings 表（之后用 Workbench 跑 04_分析.sql）

原理：
  SQLAlchemy 是"Python ↔ 数据库"的连接管道，pymysql 是底层驱动；
  df.to_sql 一行代码把整个 DataFrame 写成数据库表。
"""
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text

# ←←← 只需要改这里：你的 MySQL root 密码
# ⚠ 以后上传 GitHub 之前，记得把这里改回占位文字，别把真实密码传上去
MYSQL_PASSWORD = "在这里填你的MySQL密码"

# 忘改密码就运行的拦截提示（否则中文密码会在连接阶段报一个看不懂的编码错误）
if "在这里填" in MYSQL_PASSWORD:
    print("你还没填密码：用记事本（或 VS Code）打开 03_导入MySQL.py，")
    print("把 MYSQL_PASSWORD 后面引号里的内容改成你的 MySQL root 密码，保存后重新运行")
    raise SystemExit(1)

CSV_FILE = Path(__file__).parent / "data" / "clean" / "jobs_clean.csv"
DB_NAME = "jobs"
TABLE_NAME = "job_postings"

df = pd.read_csv(CSV_FILE)
print(f"读取清洗后数据：{len(df)} 条")

# 密码里如果有 @ # % 之类特殊字符，直接拼进连接串会被误解析，quote_plus 做转义
pwd = quote_plus(MYSQL_PASSWORD)

try:
    # 连接串格式：协议+驱动://用户:密码@地址:端口/库名?字符集
    engine = create_engine(
        f"mysql+pymysql://root:{pwd}@localhost:3306/?charset=utf8mb4"
    )
    with engine.connect() as conn:
        # utf8mb4 才是完整的 UTF-8（utf8 在 MySQL 里最多 3 字节，存不了部分字符）
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARSET utf8mb4"))
        conn.commit()
    print("MySQL 连接成功，jobs 库已就绪")
except Exception as e:
    print(f"连接失败：{e}\n")
    print("排查三步：")
    print("  1) 密码对吗？（在 03 文件开头填的就是 root 密码）")
    print("  2) 服务在跑吗？（Win+R 输入 services.msc，找 MySQL80，状态应为'正在运行'）")
    print("  3) 还不行就把报错发给我")
    raise SystemExit(1)

# 指定库重新建连接，整表写入
# if_exists="replace"：表已存在就先删再建（重跑脚本永远得到干净表）
engine = create_engine(
    f"mysql+pymysql://root:{pwd}@localhost:3306/{DB_NAME}?charset=utf8mb4"
)
df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
print(f"已导入 {len(df)} 条 → {DB_NAME} 库的 {TABLE_NAME} 表")

# 用 SQL 反查验证（顺便预演下一课：COUNT + GROUP BY）
with engine.connect() as conn:
    total = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}")).scalar()
    cities = conn.execute(
        text(f"SELECT COUNT(DISTINCT 城市) FROM {TABLE_NAME}")
    ).scalar()
print(f"SQL 验证：COUNT(*) = {total}，覆盖 {cities} 个城市")
print("\n下一步：打开 MySQL Workbench，加载 04_分析.sql 逐段运行")
