# 2026世界杯300-agent预测系统

基于M3大模型的"群体智慧"预测实验。300个agent分成10个派别，各派别有独立的判断逻辑，独立联网检索真实数据后给冠军预测，最后加权聚合成夺冠概率榜。

**仅供娱乐**。

## 项目结构

```
worldcup2026/
├── README.md                       # 本文档
├── agents_pool.json                # 300个agent定义（10派别×30身份）
├── run_agents_v2.py                # 主agent生成脚本（M3 API）
├── retry_failed.py / retry5.py     # 补失败agent的脚本
├── retry2_final.py / retry3.py     # 极难prompt的手工补
├── agents_output.json              # 300个agent的原始输出
├── aggregate.py                    # 聚合脚本（加权+派别分析+黑马识别）
├── aggregated.json                 # 聚合结果
├── build_page.py                   # 生成网页数据
├── assemble.py                     # 组装最终HTML
├── index_template.html             # HTML模板（CSS/JS）
├── page_data.json                  # 网页数据中间产物
└── index.html                      # 最终可部署的单文件网页
```

## 10个派别（每派30人）

| 派别 | 加权逻辑 | 典型输出 |
|------|---------|---------|
| 数据派 | 身价+ELO+xG | 英格兰 |
| 赔率派 | 博彩盘口+隐含概率 | 法国 |
| 老球迷派 | 历史底蕴+大赛基因 | 法国/巴西 |
| 玄学派 | 东道主魔咒+逢偶数年 | 西班牙 |
| 主帅视角派 | 战术克制+排兵深度 | 西班牙 |
| 伤病赛程派 | 关键球员伤病+赛程难度 | 法国 |
| 黑马派 | 被低估+冷门潜力 | 日本 |
| 阵容年龄派 | 核心当打之年 | 西班牙 |
| 心理抗压派 | 点球+逆境翻盘 | 阿根廷 |
| 建模派 | 蒙特卡洛+泊松 | 法国 |

## 怎么跑（本地预览）

```bash
# 1. 生成agent判断（如果还没跑过）
export MINIMAX_API_KEY="sk-..."  # minimax的M3 API key
python3 run_agents_v2.py

# 2. 聚合
python3 aggregate.py

# 3. 生成网页
python3 build_page.py
python3 assemble.py

# 4. 打开 index.html
open index.html  # 或浏览器直接打开
```

## 关键文件说明

- `agents_pool.json`: agent身份库。结构是 `{factions: {派别名: [{id, identity, weight, focus, anchor_team}, ...]}}`
- `agents_output.json`: 300条原始判断。`results`字段是list，每条有 `{id, faction, identity, champion, top3, confidence, reason, weight_logic, focus}`
- `aggregated.json`: 聚合结果。包含 `top_probabilities`（Top榜）、`faction_summary`（派别分布）、`dark_horse`（黑马识别）、`max_favorite`（最大热门）、`champion_ranking`（完整排序）、`raw_results`
- `index.html`: 单文件可部署网页。所有数据嵌入，无外部依赖。部署到任何静态服务器都行

## 当前结果（300/300完成，2026-06-13）

| 排名 | 球队 | 加权概率 | 冠军票数 | 平均信心 |
|------|------|---------|---------|---------|
| 1 | 法国 | 21.42% | 52 | 70+ |
| 2 | 西班牙 | 16.41% | 42 | 68 |
| 3 | 阿根廷 | 13.58% | 35 | 68 |
| 4 | 英格兰 | 9.21% | 23 | 70 |
| 5 | 巴西 | 6.81% | 20 | 60 |
| 6 | 美国 | 4.82% | 14 | 60 |
| 7 | 德国 | 4.41% | 12 | 65 |
| 8 | 墨西哥 | 3.73% | 11 | 60 |

**最被低估黑马**：塞内加尔（黑马派80% vs 赔率派0%，落差80%）

## 在线访问

https://zkns1b0k06iw.space.minimaxi.com

## 技术栈

- **大模型**：minimax-M3（API）
- **API端点**：https://api.minimaxi.com/v1/chat/completions
- **HTML/CSS/JS**：纯原生，无框架依赖
- **数据格式**：JSON（agent pool/output/aggregated）+ 嵌入式 JS const

## 注意事项

- M3 API偶尔对"模仿某年XX队"的特殊人设会生成多个JSON或格式损坏，需要重试或手工补
- max_tokens=1500能稳定输出完整JSON，低于1000容易截断
- aggregated.json中的`top_probabilities`已归一化为100%占比，便于直接展示
- index.html是单文件HTML，所有CSS/JS/数据都嵌入，可直接放任何静态服务器
