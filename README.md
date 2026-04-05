# 玄境 · 热点趋势追踪系统 (Xuanjing Trend Tracker)

## 🏯 系统简介
本项目是专为单人运营的自媒体博主设计的自动化选题与分发辅助系统。
- **目标领域**：AI (灵动幽默风) & 经济新闻 (沉稳史观风)。
- **核心逻辑**：抓取全球情报 -> AI 五维评分 -> 爆款摘要 -> 多平台变阵。

## 🚀 快速启动

### 1. 环境准备
确保已安装 Python 3.10+，并在项目根目录下运行：
```bash
# 建议使用 full path 调用 python 和 pip (如果您有多个环境)
python -m pip install -r requirements.txt
```

### 2. 配置 API
`.env` 文件已配置为您提供的 **DeepSeek-V3 (火山引擎 Ark)** 接口：
- `LLM_BASE_URL`: https://ark.cn-beijing.volces.com/api/v3
- `LLM_MODEL`: deepseek-v3-2-251201

### 3. 运行情报侦察 (Backend)
该命令会抓取 Akshare 经济新闻，并对库中未评分的素材（包含您预设的信源）进行 AI 智控评分：
```bash
python main.py
```

### 4. 启动管理后台 (Frontend)
启动 Streamlit UI 界面，查看高分选题、管理情报源及审计日志：
```bash
streamlit run app.py
```

## 🛠️ 技术布局
- **侦察兵 (Collectors)**: 
    - `rss_collector.py`: 支持 RSSHub 协议，监控公众号与国外博客。
    - `akshare_collector.py`: 获取宏观经济实时快讯。
- **参谋部 (Engine)**: 
    - `scorer.py`: 基于 DeepSeek-V3 的五维评分模型，支持 AI/经济双风格 Prompt。
- **点将台 (UI)**: 
    - `app.py`: 可视化仪表盘，支持素材筛选与情报源管理。
- **刑部风控 (Risk Control)**: 
    - 严格执行“阅后即焚”逻辑，不存储原文，规避版权风险。

## 📋 当前进度
- [x] 系统架构搭建
- [x] 数据库初始化
- [x] DeepSeek-V3 接口接入
- [x] 自动化抓取与评分流程跑通
- [ ] 万能排版 (OmniFormat) 自动生成文案 (开发中)

---
**尚书令 敬上**
