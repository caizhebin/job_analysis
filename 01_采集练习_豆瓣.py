# -*- coding: utf-8 -*-
"""
01_采集练习_豆瓣.py —— 爬虫最小闭环练习（复习你本科爬虫课的内容，跑通即可，产出不进入后续分析）

练什么：
  1. requests 发 HTTP 请求拿网页 HTML
  2. BeautifulSoup 解析 HTML、用 CSS 选择器定位数据
  3. 反爬三件套：User-Agent 伪装、超时设置、time.sleep 礼貌间隔
  4. 结果存 CSV

原理一句话：浏览器里看到的网页，本质是服务器返回的一段 HTML 文本；
requests 拿到这段文本后，BeautifulSoup 把它解析成"可以按标签查找的树"，
然后你用 CSS 选择器（div.item、span.title 这种写法）把要的数据抠出来。
"""
import csv
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# 反爬第一件事：伪装成浏览器。
# 服务器通过请求头 User-Agent 识别客户端，默认的 "python-requests/2.x" 会被很多网站直接拦截
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

BASE_URL = "https://movie.douban.com/top250"
OUT_FILE = Path(__file__).parent / "data" / "raw" / "douban_top250_练习.csv"

rows = []
# 练习只爬前 2 页（每页 25 条）；想爬全 250 条把 range(2) 改成 range(10)
for page in range(2):
    # params 是查询参数：?start=25 表示从第 26 条开始（翻页就是改这个数字）
    resp = requests.get(BASE_URL, params={"start": page * 25},
                        headers=HEADERS, timeout=10)

    if resp.status_code != 200:
        # 豆瓣偶尔会拦截无 Cookie 的请求（403），这是正常现象，不代表代码错了
        print(f"第 {page + 1} 页被拦截（HTTP {resp.status_code}），"
              f"稍等几分钟重试，或直接跳过本练习——它只是练习，不影响后面的分析")
        break

    soup = BeautifulSoup(resp.text, "html.parser")

    # CSS 选择器：每部电影包在一个 class="item" 的 div 里
    for item in soup.select("div.item"):
        # split("/")[0] 是因为片名 span 里有 "肖申克的救赎 / The Shawshank..."，
        # 斜杠前才是中文主片名
        title = item.select_one("span.title").get_text().split("/")[0].strip()
        rating = item.select_one("span.rating_num").get_text()
        rows.append([title, rating])

    print(f"第 {page + 1} 页完成，累计采集 {len(rows)} 条")
    time.sleep(3)  # 反爬第二件事：控制频率。请求太快会触发风控、封 IP

if rows:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    # newline="" 防止 Windows 记事本打开出现空行；encoding="utf-8-sig" 让 Excel 打开不乱码
    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["电影名", "评分"])
        writer.writerows(rows)
    print(f"已保存到 {OUT_FILE}")
else:
    print("本次没有采集到数据（被拦截），不影响项目主线——真实数据集已在 data/raw/ 里")
