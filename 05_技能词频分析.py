# -*- coding: utf-8 -*-
"""
05_技能词频分析.py —— 本项目最有价值的分析：JD（职位描述）里各技能的出现率

运行：py 05_技能词频分析.py      （需要先跑完 02）
产出：data/clean/skill_rates.csv（给 Power BI 画条形图用）+ 控制台交叉分析

原理：
  str.contains 返回 True/False 组成的列（布尔掩码）；
  对布尔列 .mean() = True 的比例 = "出现率"。
  这是"把文本字段变成可统计字段"的最常用技巧。
"""
from pathlib import Path

import pandas as pd

CLEAN_FILE = Path(__file__).parent / "data" / "clean" / "jobs_clean.csv"
OUT_FILE = Path(__file__).parent / "data" / "clean" / "skill_rates.csv"

df = pd.read_csv(CLEAN_FILE)
print(f"读取 {len(df)} 条岗位数据\n")

# 技能清单可自行增删；英文技能用 \b 词边界，防止 "R" 误匹配到 "Report" 里的 R
SKILLS = ["SQL", "Excel", "Python", "Hadoop", "SPSS", "SAS",
          "Hive", "R", "Tableau", "BI", "PPT", "机器学习", "数据挖掘"]

rates = {}
like_rates = {}
for skill in SKILLS:
    desc = df["职位描述"]
    # 主口径：独立提及——前后不能是英文字母。
    # ⚠ 教训：最初版本用 \b{skill}\b，但 Python 把汉字也算"单词字符"，
    # "熟练Excel"里 练↔E 之间不存在词边界，导致 Excel 被低估成 7%（实际约 38%）。
    # 改用 (?<![A-Za-z])...(?![A-Za-z])：只按英文字母判边界——
    # "Oracle" 里的 R 不会误配，紧挨中文的提及能正常命中。
    pattern = rf"(?<![A-Za-z]){skill}(?![A-Za-z])"
    rates[skill] = round(desc.str.contains(pattern, case=False, na=False).mean() * 100, 1)
    # 对照口径：子串匹配——与 04_分析.sql 查询 5 的 LIKE '%skill%' 完全等价，用于交叉验证
    like_rates[skill] = round(desc.str.contains(skill, case=False, na=False, regex=False).mean() * 100, 1)

rate_df = (
    pd.DataFrame({"技能": SKILLS,
                  "JD提及率%": [rates[s] for s in SKILLS],
                  "LIKE口径%": [like_rates[s] for s in SKILLS]})
    .sort_values("JD提及率%", ascending=False)
    .reset_index(drop=True)
)

print("── 数据分析岗位 JD 技能提及率（主口径=独立提及；LIKE口径用于与SQL交叉验证）──")
print(rate_df.to_string(index=False))

rate_df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
print(f"\n已保存到 {OUT_FILE}（Power BI 条形图直接用这个文件）")

# ── 交叉分析：不同经验档位对 SQL/Python 的要求差异 ──────────────────
# groupby 布尔列 → mean() = 各组的 True 比例；这是 groupby 最重要的用法
df["要求SQL"] = df["职位描述"].str.contains(r"(?<![A-Za-z])SQL(?![A-Za-z])", case=False, na=False)
df["要求Python"] = df["职位描述"].str.contains(r"(?<![A-Za-z])Python(?![A-Za-z])", case=False, na=False)

cross = (
    df.groupby("经验要求")[["要求SQL", "要求Python"]]
    .mean()
    .round(3) * 100
).rename(columns={"要求SQL": "SQL要求率%", "要求Python": "Python要求率%"})

print("\n── 交叉分析：经验档位 × 技能要求率（看看资深岗位更看重什么）──")
print(cross.to_string())

print("\n下一步：Power BI 连接 data/clean/ 下的 CSV 出看板（步骤见 README）")
