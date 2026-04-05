import streamlit as st
import pandas as pd
import sqlite3
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.utils.orchestrator import IntelligenceOrchestrator

# Load config
load_dotenv()

st.set_page_config(page_title="玄境 · 热点趋势追踪 (Xuanjing Trend)", layout="wide")

st.title("🏯 玄境 · 热点趋势追踪系统")
st.markdown("---")

# Orchestrator instance
orchestrator = IntelligenceOrchestrator()

# DB Helper
def get_db_connection():
    return sqlite3.connect("data/news_trend.db")

# Sidebar
st.sidebar.title("🎮 操控台")
menu = st.sidebar.selectbox("切换模块", ["选题池 (Materials)", "情报源 (Sources)", "历史档案 (Archives)", "内容变阵 (Formatter)", "系统设置", "🛡️ 刑部合规提示"])

# Sidebar Audit Log
st.sidebar.markdown("---")
st.sidebar.subheader("📡 侦察兵实时状态")
conn = get_db_connection()
status_df = pd.read_sql_query("SELECT name, last_fetched_at FROM sources WHERE is_active = 1", conn)
conn.close()
if not status_df.empty:
    st.sidebar.dataframe(status_df, hide_index=True)
else:
    st.sidebar.write("暂无激活的侦察兵。")

st.sidebar.subheader("📋 近期审计记录")
conn = get_db_connection()
recent_logs = pd.read_sql_query("SELECT action, status, tokens_used, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 5", conn)
conn.close()
if not recent_logs.empty:
    st.sidebar.dataframe(recent_logs, hide_index=True)

if menu == "🛡️ 刑部合规提示":
    st.header("🛡️ 刑部合规与风控提示 (CRO Audit)")
    st.warning("⚠️ 吾皇请详阅以下三策，以保江山稳固：")
    
    st.markdown("""
    ### 1. 版权与合理使用 (Copyright & Fair Use)
    *   **阅后即焚**：系统抓取原文后，仅在内存中进行 AI 摘要，数据库**严禁存储原文全篇**。
    *   **洗炼逻辑**：所有生成的内容 must 具备“独创性视角”或“数据重构”，避免直接抄袭对标账号。
    
    ### 2. 平台合规风险 (Platform Compliance)
    *   **采集频率**：过度抓取（尤其是 X 和 微信）可能导致 IP 被封禁或账号限制。系统已预置**“冷却期”**逻辑。
    *   **发布合规**：AI 生成的内容在涉及经济数据、政治敏感点时，必须进行**“人工二审”**。
    
    ### 3. 数据隐私与安全 (Data Privacy)
    *   **APIKey 保护**：切勿将 `.env` 文件同步至公开代码库（已配置 `.gitignore`）。
    *   **审计日志**：系统已开启“刑部审计日志”，所有抓取与分发记录均可追溯。
    """)
    
    st.info("💡 刑部建议：所有涉及金钱、百分比的经济数据，系统必须标注逻辑溯源 (Logic Trace)，请务必点击核验。")
    
    st.subheader("📋 刑部实时审计日志")
    conn = get_db_connection()
    logs_df = pd.read_sql_query("SELECT action, status, details, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 20", conn)
    conn.close()
    st.dataframe(logs_df, use_container_width=True)

elif menu == "选题池 (Materials)":
    st.header("💎 高价值素材池")
    
    # 1. Immediate Action: Pending Scores (New: Force check in DB to be reactive)
    conn = get_db_connection()
    pending_count_db = conn.execute("SELECT COUNT(*) FROM materials WHERE score IS NULL").fetchone()[0]
    conn.close()
    
    if pending_count_db > 0:
        st.error(f"🚨 发现 {pending_count_db} 条素材由于抓取过快，AI 尚未完成深度研读（评分暂缺）。")
        if st.button(f"⚡ 立即启动 AI 批量研读 (消耗约 {pending_count_db*1500} tokens)", type="primary", key="btn_run_scoring_top_fixed"):
            with st.spinner("AI 正在对积压情报进行深度拆解与多维评分..."):
                scored = orchestrator.run_scoring()
                st.success(f"处理完成！本次新增评分: {scored}")
                st.rerun()
    else:
        st.success("✅ 所有素材已完成 AI 研读。")

    # 2. Scoring Algorithm Configuration (Explicit Formula)
    with st.expander("⚖️ 评分权重配置 (Scoring Algorithm)", expanded=False):
        st.write("调整各维度权重，实时重新计算素材得分。")
        col1, col2, col3 = st.columns(3)
        with col1:
            w_novelty = st.slider("新奇度 (Novelty)", 0.0, 5.0, 1.0, 0.1)
            w_utility = st.slider("实用性 (Utility)", 0.0, 5.0, 2.0, 0.1)
        with col2:
            w_resonance = st.slider("共鸣感 (Resonance)", 0.0, 5.0, 1.0, 0.1)
            w_talkability = st.slider("谈资度 (Talkability)", 0.0, 5.0, 1.5, 0.1)
        with col3:
            w_actionability = st.slider("可执行性 (Actionability)", 0.0, 5.0, 2.5, 0.1)
            w_time = st.slider("时间权重 (Time Decay)", 0.0, 2.0, 0.5, 0.1)
        
        st.info(f"**当前公式:** $Score = \\frac{{{w_novelty}N + {w_utility}U + {w_resonance}R + {w_talkability}T + {w_actionability}A}}{{{round(w_novelty+w_utility+w_resonance+w_talkability+w_actionability, 1)}}} \\times (1 - {w_time} \\times \\frac{{HoursPassed}}{{168}})$ (一周内线性衰减)")

    # Manual Input in Sidebar
    st.sidebar.markdown("---")
    st.subheader("📥 手工提审新素材")
    manual_url = st.sidebar.text_input("粘贴文章 URL (微信/网页)")
    manual_cat = st.sidebar.selectbox("领域", ["AI", "Economy"], key="manual_cat")
    if st.sidebar.button("开始提审"):
        if manual_url:
            with st.spinner("锦衣卫正在秘密解析内容并进行 AI 评分..."):
                res = orchestrator.process_single_url(manual_url, manual_cat)
                if res:
                    st.success(f"素材已入库并评分！总分: {res.get('score', 'N/A')}")
                    st.rerun()
                else:
                    st.error("提审失败，请检查 URL 或 API 配置。")
        else:
            st.warning("请先输入有效 URL。")

    # Table of materials
    conn = get_db_connection()
    materials_df = pd.read_sql_query("""
        SELECT id, title, url, category, score, reasoning, created_at, score_details
        FROM materials 
    """, conn)
    conn.close()
    
    if not materials_df.empty:
        # Dynamic Scoring Logic
        def calculate_dynamic_score(row):
            # Check for NULL/None/NaN in the score column
            if pd.isnull(row['score']):
                return -1.0  # Use -1 to indicate Pending (ensure float type)
            try:
                details_json = json.loads(row['score_details']) if row['score_details'] else {}
                # Handle nested or flat JSON
                def get_s(key):
                    val = details_json.get('details', details_json).get(key, 0)
                    return val.get('score', 0) if isinstance(val, dict) else val
                
                n = get_s('novelty')
                u = get_s('utility')
                r = get_s('resonance')
                t = get_s('talkability')
                a = get_s('actionability')
                
                base_score = (w_novelty*n + w_utility*u + w_resonance*r + w_talkability*t + w_actionability*a)
                total_w = (w_novelty + w_utility + w_resonance + w_talkability + w_actionability)
                if total_w == 0: total_w = 1
                avg_score = base_score / total_w
                
                # Time decay (Linear decay over 1 week)
                created_at = datetime.strptime(row['created_at'], "%Y-%m-%d %H:%M:%S")
                hours_passed = (datetime.now() - created_at).total_seconds() / 3600
                time_factor = max(0.1, 1 - (w_time * min(hours_passed, 168) / 168))
                
                return round(avg_score * time_factor, 2)
            except Exception as e:
                # Ensure we always return a float value
                try:
                    return float(row['score']) if row['score'] is not None else -1.0
                except:
                    return -1.0

        materials_df['动态评分'] = materials_df.apply(calculate_dynamic_score, axis=1)
        
        # Display Status Metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        pending_count = (materials_df['动态评分'] < 0).sum()
        col_m1.metric("总素材数", len(materials_df))
        col_m2.metric("待评分 (Pending AI)", pending_count)
        col_m3.metric("平均评分", f"{materials_df[materials_df['动态评分'] >= 0]['动态评分'].mean():.2f}")
        
        st.markdown("---")
        # Filtering & Sorting
        col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
        with col_f1:
            sort_by = st.selectbox("排序方式", ["动态评分 (高->低)", "动态评分 (低->高)", "发布时间 (新->旧)", "发布时间 (旧->新)"])
        with col_f2:
            filter_cat = st.multiselect("过滤领域", ["AI", "Economy"], default=["AI", "Economy"])
        with col_f3:
            search_q = st.text_input("搜索标题", "")

        # Apply Filters
        filtered_df = materials_df[materials_df['category'].isin(filter_cat)]
        if search_q:
            filtered_df = filtered_df[filtered_df['title'].str.contains(search_q, case=False)]
        
        # Apply Sorting
        sort_map = {
            "动态评分 (高->低)": ("动态评分", False),
            "动态评分 (低->高)": ("动态评分", True),
            "发布时间 (新->旧)": ("created_at", False),
            "发布时间 (旧->新)": ("created_at", True)
        }
        s_col, s_asc = sort_map[sort_by]
        filtered_df = filtered_df.sort_values(by=s_col, ascending=s_asc)

        # Replace -1 with "待评分" for display (ensure all values are strings to avoid Arrow type conflicts)
        display_df = filtered_df.copy()
        display_df['显示评分'] = display_df['动态评分'].apply(lambda x: "⏳ 研读中..." if x == -1 else str(x))

        st.dataframe(
            display_df[['id', 'title', 'url', 'category', '显示评分', 'created_at']], 
            column_config={
                "url": st.column_config.LinkColumn("原文链接"),
                "显示评分": st.column_config.TextColumn("动态评分 (含时间衰减)")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Detailed View
        st.markdown("---")
        st.subheader("🔍 选题深度拆解 (Transparency Report)")
        selected_id = st.selectbox("选择要审阅的素材 ID", filtered_df['id'].tolist())
        
        conn = get_db_connection()
        item = conn.execute("SELECT * FROM materials WHERE id = ?", (selected_id,)).fetchone()
        columns = [description[0] for description in conn.execute("SELECT * FROM materials LIMIT 1").description]
        item_dict = dict(zip(columns, item))
        conn.close()
        
        if item_dict.get('score_details'):
            try:
                details_json = json.loads(item_dict['score_details'])
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"### {item_dict['title']}")
                    st.caption(f"领域: {item_dict['category']} | 原始分: {item_dict['score']} | 抓取时间: {item_dict['created_at']}")
                    st.markdown(f"**情报摘要:** {item_dict.get('content_summary', '无摘要')}")
                    st.markdown(f"**打分理由:** {item_dict.get('reasoning', '无理由')}")
                    
                    st.write("#### ⚖️ 五维打分细节")
                    dim_data = []
                    dim_labels = {
                        "novelty": "新奇度",
                        "utility": "实用性",
                        "resonance": "共鸣感",
                        "talkability": "谈资度",
                        "actionability": "可执行性"
                    }
                    
                    dim_dict = details_json.get('details', details_json) 
                    for dim_key, data in dim_dict.items():
                        dim_label = dim_labels.get(dim_key.lower(), dim_key)
                        if isinstance(data, dict):
                            dim_data.append({"维度": dim_label, "得分": data.get('score'), "判定理由": data.get('justification')})
                        else:
                            dim_data.append({"维度": dim_label, "得分": data, "判定理由": "早期数据无记录"})
                    st.table(dim_data)
                
                with col2:
                    st.write("#### ✅ 核心亮点 (Plus)")
                    for p in details_json.get('plus_points', ["无"]):
                        st.success(p)
                    
                    st.write("#### ❌ 潜在短板 (Minus)")
                    for m in details_json.get('minus_points', ["无"]):
                        st.error(m)
                        
                    st.link_button("🔗 访问原文", item_dict['url'])
                    
                    # Manual Delete & Reread Buttons
                    st.markdown("---")
                    st.write("#### 🛠️ 运维操作 (Operations)")
                    col_op1, col_op2 = st.columns(2)
                    with col_op1:
                        if st.button("🔄 强制重读与评分", key=f"force_reread_{selected_id}"):
                            with st.spinner("正在强制重新解析并评分..."):
                                success = orchestrator.reread_material(selected_id)
                                if success:
                                    st.success(f"素材 [ID: {selected_id}] 已重读并重新评分。")
                                    st.rerun()
                                else:
                                    st.error("重读失败，请检查 URL。")
                    
                    with col_op2:
                        if st.button("🔴 永久删除素材", key=f"del_{selected_id}", type="primary"):
                            conn = get_db_connection()
                            conn.execute("DELETE FROM materials WHERE id = ?", (selected_id,))
                            conn.commit()
                            conn.close()
                            st.success(f"素材 [ID: {selected_id}] 已从池中移除。")
                            st.rerun()
            except Exception as e:
                st.error(f"解析打分细节时出错: {e}")
        else:
            st.info("该素材尚未完成 AI 评分或数据格式较旧。")
    else:
        st.write("目前池中尚无素材。")

elif menu == "情报源 (Sources)":
    st.header("🔍 情报源管理 (Intelligence Sources)")
    st.write("配置 RSS、WeChat、Twitter 等情报侦察点。")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📡 侦察兵列表")
        conn = get_db_connection()
        sources_df = pd.read_sql_query("SELECT id, name, type, url_or_key, category, is_active, last_fetched_at FROM sources", conn)
        conn.close()
        st.dataframe(sources_df, use_container_width=True, hide_index=True)
        
        if st.button("🔄 立即运行全量抓取"):
            with st.spinner("调度各路侦察兵潜入中..."):
                saved, scored = orchestrator.crawl_all_active()
                st.success(f"任务完成！捕获新素材: {saved}，完成 AI 评分: {scored}")
                st.rerun()

    with col2:
        st.subheader("➕ 招募新侦察兵")
        with st.form("add_source_form"):
            source_name = st.text_input("名称 (例如：数字生命卡兹克)")
            source_type = st.selectbox("类型", ["X (Twitter)", "RSS (Blog/Arxiv)", "WeChat (RSS)", "Akshare", "Weibo"])
            source_url = st.text_input("URL/Key (Weibo请填UID)")
            source_cat = st.selectbox("默认领域", ["AI", "Economy"])
            if st.form_submit_button("入库"):
                conn = get_db_connection()
                conn.execute("INSERT INTO sources (name, type, url_or_key, category) VALUES (?, ?, ?, ?)", 
                             (source_name, source_type, source_url, source_cat))
                conn.commit()
                conn.close()
                st.success(f"侦察兵 {source_name} 已就位！")
                st.rerun()

elif menu == "历史档案 (Archives)":
    st.header("📚 历史纵深检索 (Historical Archives)")
    st.write("针对高价值账号执行历史全量追溯任务。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 发起追溯任务")
        conn = get_db_connection()
        sources = pd.read_sql_query("SELECT id, name FROM sources", conn)
        conn.close()
        
        target_source = st.selectbox("选择目标情报源", sources['name'].tolist())
        target_id = sources[sources['name'] == target_source]['id'].values[0]
        
        if st.button("🚀 开始历史追溯"):
            task_id = orchestrator.create_historical_task(int(target_id), target_source)
            st.success(f"追溯任务已在后台启动 (ID: {task_id})")

    with col2:
        st.subheader("⏳ 正在运行的追溯任务")
        conn = get_db_connection()
        tasks_df = pd.read_sql_query("SELECT id, source_name, progress, status, last_message, created_at FROM background_tasks ORDER BY created_at DESC", conn)
        conn.close()
        
        if not tasks_df.empty:
            st.dataframe(tasks_df, use_container_width=True, hide_index=True)
            
            # Cleanup Section for Tasks
            with st.expander("🗑️ 清理追溯任务"):
                col_d1, col_d2 = st.columns([2, 1])
                with col_d1:
                    task_to_del_name = st.selectbox("选择要清理的任务", tasks_df['source_name'].tolist(), key="del_task_select")
                    task_to_del_id = tasks_df[tasks_df['source_name'] == task_to_del_name]['id'].values[0]
                with col_d2:
                    st.write("")
                    st.write("")
                    if st.button("确认清理", type="primary", key="btn_del_task"):
                        conn = get_db_connection()
                        conn.execute("DELETE FROM background_tasks WHERE id = ?", (int(task_to_del_id),))
                        conn.execute("DELETE FROM task_logs WHERE task_id = ?", (int(task_to_del_id),))
                        conn.commit()
                        conn.close()
                        st.success(f"任务已清理。")
                        st.rerun()
                
                if st.button("🧹 一键清理所有已结束任务"):
                    conn = get_db_connection()
                    conn.execute("DELETE FROM background_tasks WHERE status IN ('failed', 'completed')")
                    conn.execute("DELETE FROM task_logs WHERE task_id NOT IN (SELECT id FROM background_tasks)")
                    conn.commit()
                    conn.close()
                    st.success("历史任务已清理。")
                    st.rerun()
        else:
            st.info("当前无后台任务。")

elif menu == "内容变阵 (Formatter)":
    st.header("✍️ 自动化内容变阵 (OmniFormat)")
    st.write("选择高分素材，利用 AI 自动生成适配不同平台的文案。")
    
    conn = get_db_connection()
    materials_df = pd.read_sql_query("SELECT id, title, score, category FROM materials WHERE score IS NOT NULL ORDER BY score DESC", conn)
    conn.close()
    
    if not materials_df.empty:
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_material_id = st.selectbox("选择素材", materials_df['id'].tolist(), format_func=lambda x: f"ID {x}: {materials_df[materials_df['id']==x]['title'].values[0][:30]}...")
            platform = st.selectbox("选择发布平台", ["X", "LinkedIn", "WeChat", "Substack"])
            
            if st.button("🚀 生成文案"):
                with st.spinner(f"正在为 {platform} 平台进行文案创作..."):
                    from src.engine.formatter import OmniFormatter
                    formatter = OmniFormatter()
                    draft = formatter.generate_draft(selected_material_id, platform)
                    if draft:
                        st.success("文案生成成功！")
                    else:
                        st.error("文案生成失败。")
        
        with col2:
            st.subheader("📝 平台草稿箱")
            conn = get_db_connection()
            drafts_df = pd.read_sql_query("""
                SELECT d.id, m.title, d.platform, d.content, d.created_at 
                FROM drafts d
                JOIN materials m ON d.material_id = m.id
                WHERE d.material_id = ?
                ORDER BY d.created_at DESC
            """, conn, params=(int(selected_material_id),))
            conn.close()
            
            if not drafts_df.empty:
                for idx, row in drafts_df.iterrows():
                    with st.expander(f"{row['platform']} 草稿 - {row['created_at']}"):
                        st.text_area("文案内容", value=row['content'], height=300, key=f"draft_{row['id']}")
            else:
                st.info("该素材暂无草稿。")
    else:
        st.write("目前尚无已评分素材。")

elif menu == "系统设置":
    st.header("⚙️ 系统配置与财务审计 (Hubu Audit)")
    
    # Token Budget Section
    st.subheader("💰 令牌预算 (Token Budget)")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    total_tokens_24h = conn.execute("SELECT SUM(tokens_used) FROM audit_logs WHERE created_at > ?", (yesterday,)).fetchone()[0] or 0
    conn.close()
    
    col1, col2 = st.columns(2)
    col1.metric("24小时令牌消耗", f"{total_tokens_24h:,}")
    col2.metric("日均预算上限", f"{orchestrator.token_limit_daily:,}")
    
    budget_progress = min(total_tokens_24h / orchestrator.token_limit_daily, 1.0)
    st.progress(budget_progress, text=f"预算使用率: {budget_progress*100:.1f}%")
    
    if budget_progress > 0.8:
        st.warning("⚠️ 警告：令牌预算即将耗尽。")

    st.markdown("---")
    st.subheader("⏰ 自动化任务调度 (Scheduler Status)")
    conn = get_db_connection()
    last_run = conn.execute("SELECT created_at FROM audit_logs WHERE action='scraping' ORDER BY created_at DESC LIMIT 1").fetchone()
    conn.close()
    
    if last_run:
        st.success(f"📡 调度系统活跃中。最近一次抓取时间: {last_run[0]}")
    else:
        st.warning("📡 尚未发现调度运行记录。")

    st.write("如需实现全自动定时抓取，请在后台运行：")
    st.code("python scheduler.py", language="bash")
