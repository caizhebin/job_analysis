# -*- coding: utf-8 -*-
"""临时诊断脚本：验证 04_分析.sql 各查询的正确结果（以 CSV 为唯一事实来源）"""
import pandas as pd

df = pd.read_csv(r"C:\Users\蔡哲斌\Desktop\job_analysis\data\clean\jobs_clean.csv")
desc = df["职位描述"]

print(f"总岗位数: {len(df)}\n")

# ── 查询 1 城市表（HAVING >= 10）──────────────────────────────────────
city = (df.groupby("城市")
          .agg(岗位数=("城市", "size"), 平均薪资_千=("薪资中值", "mean"))
          .round(1))
print("── 查询 1 真实结果：城市 × 岗位数 × 平均薪资（仅岗位数≥10）──")
print(city[city["岗位数"] >= 10].sort_values("岗位数", ascending=False).to_string())
big3 = city.loc[["北京", "上海", "深圳"], "岗位数"].sum() if set(["北京", "上海", "深圳"]) <= set(city.index) else None
print(f"北上深合计: {big3} 条，占 {big3 / len(df) * 100:.0f}%\n" if big3 else "")

# ── 查询 3 经验 × 薪资 ────────────────────────────────────────────────
print("── 查询 3 真实结果：经验要求 × 平均薪资 ──")
print(df.groupby("经验要求")
        .agg(岗位数=("经验要求", "size"), 平均薪资_千=("薪资中值", "mean"))
        .round(1)
        .sort_values("平均薪资_千", ascending=False)
        .to_string())
print()

# ── 查询 4 岗位类别 × 薪资（HAVING >= 10）────────────────────────────
cat = (df.groupby("岗位类别")
         .agg(岗位数=("岗位类别", "size"), 平均薪资_千=("薪资中值", "mean"))
         .round(1))
print("── 查询 4 真实结果：岗位类别 × 平均薪资（仅岗位数≥10）──")
cat_f = cat[cat["岗位数"] >= 10].sort_values("平均薪资_千", ascending=False)
print(cat_f.to_string())
if "数据分析" in cat_f.index and "数据工程" in cat_f.index:
    ratio = cat_f.loc["数据工程", "平均薪资_千"] / cat_f.loc["数据分析", "平均薪资_千"]
    print(f"数据工程 / 数据分析 薪资比: {ratio:.1f} 倍\n")

# ── 技能词频两种口径 ──────────────────────────────────────────────────
skills = ["SQL", "Excel", "Python", "Hadoop", "SPSS", "SAS",
          "Hive", "R", "Tableau", "BI", "PPT", "数据挖掘", "机器学习"]
print("── 技能词频：LIKE子串口径(与SQL查询5一致) vs 独立提及口径 ──")
for s in skills:
    sub = desc.str.contains(s, case=False, na=False, regex=False).sum()
    loo = desc.str.contains(rf"(?<![A-Za-z]){s}(?![A-Za-z])",
                            case=False, na=False, regex=True).sum()
    print(f"{s:<10} LIKE口径 {sub:>4} ({sub / len(df) * 100:5.1f}%)   "
          f"独立口径 {loo:>4} ({loo / len(df) * 100:5.1f}%)")
