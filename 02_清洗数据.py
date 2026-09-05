# -*- coding: utf-8 -*-
"""
02_清洗数据.py —— 把原始 xlsx 清洗成分析可用的干净 CSV（项目主线第一步）

运行：py 02_清洗数据.py        （在项目文件夹里运行）
产出：data/clean/jobs_clean.csv + 控制台打印"清洗口径"

口径记录（原始数据多少条、每步删了多少、依据是什么，都要能说清楚）：
  - 原始 589 条，"职位名称+公司"重复的删掉
  - 薪资解析成区间："10k-20k" → 下限 10 / 上限 20 / 中值 15（千/月），
    面议等解析不出的剔除；未计入年终奖系数
"""
from pathlib import Path

import pandas as pd

RAW_FILE = Path(__file__).parent / "data" / "raw" / "Data_Lagou.xlsx"
OUT_FILE = Path(__file__).parent / "data" / "clean" / "jobs_clean.csv"

# ── 原始列名 → 标准中文列名 ─────────────────────────────────────────────
# 换新数据集时只需要改这张映射表 + RAW_FILE，脚本其余部分不用动
COLUMN_MAP = {
    "title": "职位名称",
    "month_salary": "薪资",
    "company": "公司",
    "industry": "行业",
    "scale": "公司规模",
    "phase": "融资阶段",
    "city": "城市",
    "experience": "经验要求",
    "qualification": "学历要求",
    "full_or_parttime": "工作性质",
    "description": "职位描述",
}

df = pd.read_excel(RAW_FILE)
print(f"原始数据：{len(df)} 行 × {df.shape[1]} 列")

# ── 第 1 步：只保留映射表里的列 ────────────────────────────────────────
# 爬虫内部字段（_clueid、_pageno 等）对分析没用，直接丢弃
df = df[list(COLUMN_MAP)].rename(columns=COLUMN_MAP)

# ── 第 2 步：去重 ──────────────────────────────────────────────────────
# 依据："职位名称 + 公司" 组合相同视为同一条岗位的重复抓取
before = len(df)
df = df.drop_duplicates(subset=["职位名称", "公司"])
print(f"去重：删除 {before - len(df)} 条（职位名称+公司 重复）")

# ── 第 3 步：缺失值 ────────────────────────────────────────────────────
# 薪资/城市/职位描述 为空的行无法参与核心分析，删除——每删一类都要记进"口径"
before = len(df)
df = df.dropna(subset=["薪资", "城市", "职位描述"])
print(f"缺失值：删除 {before - len(df)} 条（薪资/城市/职位描述 为空）")

# ── 第 4 步：解析薪资（本项目最重要的一步）─────────────────────────────
# "10k-20k" → 薪资下限=10、薪资上限=20、薪资中值=15（千/月）
# str.extract 里的两个括号是正则"捕获组"，分别抓出两个数字，直接生成两列
df[["薪资下限", "薪资上限"]] = (
    df["薪资"]
    .astype(str)
    .str.extract(r"(\d+)\s*[kK]?\s*[-~]\s*(\d+)\s*[kK]?")
    .astype(float)
)

# 解析不出数字的（"面议"、"10k以上" 等）会变成 NaN，统计数量后剔除
unparsed = int(df["薪资下限"].isna().sum())
df = df.dropna(subset=["薪资下限"])
print(f"薪资解析：{unparsed} 条无法解析（面议/10k以上等格式），已剔除")

df["薪资下限"] = df["薪资下限"].astype(int)
df["薪资上限"] = df["薪资上限"].astype(int)
# 口径说明：取区间中点代表该岗位薪资水平，未计入年终奖系数（如 ·13 薪）
df["薪资中值"] = (df["薪资下限"] + df["薪资上限"]) / 2

# ── 第 5 步：城市与行业整理 ────────────────────────────────────────────
# fillna 先兜底再转字符串：直接 astype(str) 会把空值变成 "nan" 字符串
df["城市"] = df["城市"].fillna("未知").astype(str).str.split("·").str[0].str.replace("市", "", regex=False)
# 行业是多标签（"教育,移动互联网"），取第一个作为主行业
df["主行业"] = df["行业"].fillna("未知").astype(str).str.split(",").str[0]

# ── 第 6 步：给职位打类别标签（为了"哪类数据岗薪资更高"这个分析维度）───
# .apply 是"逐行应用函数"：比向量化操作慢，但逻辑复杂时更灵活
def tag_position(name: str) -> str:
    """按关键词把职位名归到子类别，顺序即优先级（更具体的标签放前面）"""
    for keyword, tag in [
        ("产品经理", "数据产品"),
        ("挖掘", "算法/挖掘"),
        ("BI", "BI/报表"),
        ("工程师", "数据工程"),
        ("分析", "数据分析"),
    ]:
        if keyword in name:
            return tag
    return "其他/运营"

df["岗位类别"] = df["职位名称"].apply(tag_position)

# ── 保存 ────────────────────────────────────────────────────────────────
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
# encoding="utf-8-sig"：带 BOM 的 UTF-8，保证 Excel 双击打开中文不乱码
df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n清洗完成：{len(df)} 条 → {OUT_FILE}")
print("\n── 清洗后数据概览（describe 是最快了解数值分布的方式）──")
print(df["薪资中值"].describe().round(1))
print("\n── 各岗位类别数量 ──")
print(df["岗位类别"].value_counts())
print("\n下一步：运行 03_导入MySQL.py（先把里面的 MySQL 密码改成你的）")
