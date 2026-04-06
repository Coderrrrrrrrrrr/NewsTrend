# 玄境 · 热点趋势追踪系统 (Xuanjing Trend Tracker) V2.0

## 🏯 系统简介
本项目是专为单人运营的自媒体博主设计的自动化选题与分发辅助系统。
- **目标领域**：AI (灵动幽默风) & 经济新闻 (沉稳史观风)。
- **核心逻辑**：全球情报猎杀 -> 多重人格审计 -> 视觉逻辑预制 -> 多端内容变阵。

## 🚀 核心功能 (V2.0 升级)

### 1. 👁️ “天眼”主动探测器 (Heavenly Eye)
不再死守 RSS。系统利用 LLM 每日生成前沿趋势关键词，主动在全球搜索引擎中“猎杀”尚未被大众发觉的深层情报。
- **模块**: `src/collectors/agent_search.py`
- **能力**: 跨语种趋势对齐，发现“水面下”的爆款。

### 2. 🏛️ “众议院”多重人格审计 (House of Representatives)
引入“代理式评价 (Agentic Evaluation)”。针对高分素材，自动召集 **【技术极客】**、**【商业策略家】**、**【社交达人】** 进行交叉辩论。
- **模块**: `src/engine/scorer.py` & `persona_prompts.py`
- **收益**: 预判读者爽点与槽点，在动笔前即完成舆论压力测试。

### 3. 🎨 “造办处”视觉逻辑预制 (Imperial Workshop)
选题即成品。系统在评分时同步提取内容金句，并自动生成 DALL-E 3 / Midjourney 封面图提示词。
- **收益**: 视觉溢价，将 4 小时的创作时间压缩至 30 分钟。

## 🛠️ 快速启动

### 1. 环境准备
确保已安装 Python 3.10+，并运行：
```bash
python -m pip install -r requirements.txt
```

### 2. 运行情报侦察 (Backend)
该命令会触发所有活跃源（含“天眼”主动搜索）的抓取与多重人格评分：
```bash
python main.py
```

### 3. 启动管理后台 (Frontend)
查看“众议院”审计报告与视觉预制提示词：
```bash
streamlit run app.py
```

## 📋 技术布局
- **侦察兵 (Collectors)**: RSS, Akshare, Weibo, Agent Search.
- **参谋部 (Engine)**: Scorer (Multi-Persona), Formatter (OmniFormat).
- **点将台 (UI)**: Streamlit Dashboard.
- **风控 (Audit)**: Token Budget 监控 & 安全抓取 (SafeFetcher).

---
**尚书令 敬上**
