# 拉勾网数据分析岗位招聘数据分析

分析拉勾网"数据分析"相关岗位的公开招聘数据，清洗后从城市、学历、经验、
岗位类别、技能要求几个维度做统计，最后用 Power BI 做了交互看板。

## 项目结构

```
job_analysis/
├── 01_采集练习_豆瓣.py      # 练手写的爬虫（豆瓣 Top250，练习用，与主线无关）
├── 02_清洗数据.py           # 原始 xlsx → 清洗后的 jobs_clean.csv
├── 03_导入MySQL.py          # 清洗结果导入 MySQL（运行前填自己的 root 密码）
├── 04_分析.sql              # 7 段查询，在 Workbench 里逐段执行
├── 05_技能词频分析.py       # JD 文本里的技能提及率统计
├── 诊断_两种口径对比.py      # 用 CSV 重算各查询结果，做交叉核对用
├── requirements.txt
├── 看板.pbix                # Power BI 报表
└── data/
    ├── raw/Data_Lagou.xlsx          # 原始数据
    └── clean/jobs_clean.csv 等      # 清洗产物
```

## 环境

Python 3.12（pandas / requests / pymysql / sqlalchemy / beautifulsoup4 / openpyxl）、
MySQL 8.0、Power BI Desktop。

## 运行步骤

```
py 02_清洗数据.py        # 589 条 → 清洗后 543 条
# 编辑 03_导入MySQL.py 填入 MySQL 密码后：
py 03_导入MySQL.py       # 导入 jobs 库 job_postings 表
# Workbench 里打开 04_分析.sql 逐段执行
py 05_技能词频分析.py
# 看板.pbix 用 Power BI Desktop 打开（连接 data/clean 下的 CSV）
```

## 数据说明

- 来源：GitHub 公开数据集 [BigCarrey/Data_analysis_in_lagou](https://github.com/BigCarrey/Data_analysis_in_lagou)（Data_Lagou.xlsx），
  拉勾网"数据分析"类岗位，2016-09 抓取，589 条
- 清洗：按"职位名称+公司"去重删 45 条，剔除 1 条无法解析薪资的，剩 543 条
- 薪资口径："10k-20k"解析后取区间中值（单位千/月），面议等格式剔除

## 主要结果

- 城市：北上深合计约 73% 的岗位，但平均薪资深圳（16.0k）> 北京（14.0k）> 上海（12.9k），
  岗位数量和薪资高低并不同向
- 经验：应届 5.8k → 1-3 年 10.8k → 3-5 年 17.2k → 5-10 年 27.1k
- 岗位类别（只看样本 ≥10 的组）：数据工程 16.4k > 算法/挖掘 14.8k > 数据分析 12.2k
- JD 技能提及率：SQL 40%、Excel 38%、数据挖掘 34%、SAS/SPSS 约 27%、Python 20%。
  2016 年 SAS/SPSS 占比还高于 Python，和现在的招聘要求对比挺有意思

## 过程中踩的坑

1. 小样本组均值失真：比如"其他/运营"类只有 2 条岗位，平均薪资被单个高薪样本拉到 59.5k。
   后面所有 GROUP BY 聚合都加了 HAVING COUNT(*) >= 10
2. 正则词边界：`\bExcel\b` 匹配不到"熟练Excel"，因为 Python 把汉字也当单词字符，
   练和 E 之间没有词边界，导致 Excel 提及率被算成 7%。改成 `(?<![A-Za-z])Excel(?![A-Za-z])`
   只按英文字母判边界后修正为 38%
3. 统计口径：SQL 的 `LIKE '%SQL%'` 会把"MySQL"一起算进去（44%），按独立词统计是 40%。
   两种结果都保留在 05 的输出里，注明口径
4. 最早的数据结论是看 Workbench 截图记录的，后来发现读数有错（把查询 4 的结果看串了行），
   改成直接对 CSV 重算核对（诊断_两种口径对比.py 就是干这个的），以后读数一律以重算为准
