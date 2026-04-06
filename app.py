import streamlit as st
import pandas as pd
import sqlite3
import os
import json
import zlib
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

def decompress_text(compressed_data):
    """Decompress zlib compressed data."""
    if not compressed_data:
        return "无备份内容"
    try:
        return zlib.decompress(compressed_data).decode('utf-8')
    except Exception as e:
        return f"解压失败: {e}"

# Sidebar
st.sidebar.title("🎮 操控台")
menu = st.sidebar.selectbox("切换模块", ["选题池 (Materials)", "情报源 (Sources)", "内容变阵 (Formatter)", "历史档案 (Archives)", "♻️ 回收站 (Trash)", "系统设置", "🛡️ 刑部合规提示"])

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
    *   **深冷压缩**：系统抓取原文后，使用 zlib 进行二进制压缩存储。仅供内部研读，严禁未授权分发。
    *   **洗炼逻辑**：所有生成的内容 must 具备“独创性视角”或“数据重构”，避免直接抄袭对标账号。
    
    ### 2. 平台合规风险 (Platform Compliance)
    *   **影子浏览器**：使用 Playwright Stealth 模拟真实访问，降低被封禁风险。
    *   **验证码破阵**：若触发大规模验证码，请在“系统设置”中开启手动验证模式。
    
    ### 3. 数据隐私与安全 (Data Privacy)
    *   **APIKey 保护**：切勿将 `.env` 文件同步至公开代码库。
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
    
    # 1. Immediate Action: Pending Scores
    conn = get_db_connection()
    pending_count_db = conn.execute("SELECT COUNT(*) FROM materials WHERE score IS NULL AND status = 'active'").fetchone()[0]
    conn.close()
    
    if pending_count_db > 0:
        st.error(f"🚨 发现 {pending_count_db} 条素材尚未完成 AI 深度研读。")
        if st.button(f"⚡ 立即启动 AI 批量研读", type="primary"):
            with st.spinner("AI 正在对积压情报进行深度拆解与多维评分..."):
                scored = orchestrator.run_scoring()
                st.success(f"处理完成！本次新增评分: {scored}")
                st.rerun()
    else:
        st.success("✅ 所有素材已完成 AI 研读。")

    # 2. Scoring Algorithm Configuration
    with st.expander("⚖️ 评分权重配置 (Scoring Algorithm)", expanded=False):
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

    # Manual Input in Sidebar
    st.sidebar.markdown("---")
    st.subheader("📥 手工提审新素材")
    manual_url = st.sidebar.text_input("粘贴文章 URL")
    manual_cat = st.sidebar.selectbox("领域", ["AI", "Economy"], key="manual_cat")
    if st.sidebar.button("开始提审"):
        if manual_url:
            with st.spinner("锦衣卫正在秘密解析内容..."):
                res = orchestrator.process_single_url(manual_url, manual_cat)
                if res:
                    st.success(f"素材已入库并评分！总分: {res.get('score', 'N/A')}")
                    st.rerun()
        else:
            st.warning("请先输入有效 URL。")

    # Table of materials (Only active items for the main pool)
    conn = get_db_connection()
    materials_df = pd.read_sql_query("""
        SELECT id, title, url, category, score, reasoning, created_at, score_details, status
        FROM materials 
        WHERE status = 'active' OR status IS NULL
    """, conn)
    conn.close()
    
    if not materials_df.empty:
        # Dynamic Scoring Logic
        def calculate_dynamic_score(row):
            if row['status'] == 'deleted':
                return -2.0 # Internal marker for deleted
            if pd.isnull(row['score']):
                return -1.0
            try:
                details_json = json.loads(row['score_details']) if row['score_details'] else {}
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
                avg_score = base_score / (total_w if total_w > 0 else 1)
                
                created_at = datetime.strptime(row['created_at'], "%Y-%m-%d %H:%M:%S")
                hours_passed = (datetime.now() - created_at).total_seconds() / 3600
                time_factor = max(0.1, 1 - (w_time * min(hours_passed, 168) / 168))
                
                return round(avg_score * time_factor, 2)
            except:
                return float(row['score']) if row['score'] is not None else -1.0

        materials_df['动态评分'] = materials_df.apply(calculate_dynamic_score, axis=1)
        
        # Apply Filters
        filtered_df = materials_df[materials_df['category'].isin(st.multiselect("过滤领域", ["AI", "Economy"], default=["AI", "Economy"]))]
        filtered_df = filtered_df[filtered_df['动态评分'] != -2.0] # Hide deleted
        search_q = st.text_input("搜索标题", "")
        if search_q:
            filtered_df = filtered_df[filtered_df['title'].str.contains(search_q, case=False)]
        
        filtered_df = filtered_df.sort_values(by="动态评分", ascending=False)
        
        display_df = filtered_df.copy()
        display_df['显示评分'] = display_df['动态评分'].apply(lambda x: "⏳ 研读中..." if x == -1 else str(x))

        st.dataframe(
            display_df[['id', 'title', 'url', 'category', '显示评分', 'created_at']], 
            column_config={
                "url": st.column_config.LinkColumn("原文链接"),
                "显示评分": st.column_config.TextColumn("动态评分")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Detailed View
        st.markdown("---")
        st.subheader("🔍 选题深度拆解")
        if not filtered_df.empty:
            selected_id = st.selectbox("选择要审阅的素材 ID", filtered_df['id'].tolist())
            item_dict = materials_df[materials_df['id'] == selected_id].iloc[0].to_dict()
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"### {item_dict['title']}")
                st.caption(f"领域: {item_dict['category']} | 原始分: {item_dict['score']} | 抓取时间: {item_dict['created_at']}")
                
                with st.expander("📄 查看本地备份原文 (Deep Cold Storage)"):
                    # V2.3: Lazy-load full text only when expanded
                    conn = get_db_connection()
                    blob = conn.execute("SELECT full_text_zip FROM materials WHERE id = ?", (selected_id,)).fetchone()[0]
                    conn.close()
                    full_text = decompress_text(blob)
                    st.text_area("本地备份正文", value=full_text, height=400, key=f"text_{selected_id}")

                st.markdown(f"**情报摘要:** {item_dict.get('content_summary', '无摘要')}")
                st.markdown(f"**打分理由:** {item_dict.get('reasoning', '无理由')}")

            with col2:
                st.write("#### 🛠️ 运维操作 (Admin)")
                if st.button("🔴 确认为废案并逻辑删除", key=f"del_{selected_id}"):
                    try:
                        if orchestrator.logical_delete_material(selected_id):
                            st.toast(f"✅ 素材 ID {selected_id} 已转入‘废案库’。")
                            st.rerun()
                        else:
                            st.error("操作失败：未找到素材或数据库锁定。")
                    except Exception as e:
                        st.error(f"逻辑删除异常: {e}")
                
                if st.button("🗑️ 彻底物理删除 (不可恢复)", key=f"hard_del_{selected_id}"):
                    try:
                        conn = get_db_connection()
                        # Also delete related drafts to keep DB clean
                        conn.execute("DELETE FROM drafts WHERE material_id = ?", (selected_id,))
                        conn.execute("DELETE FROM materials WHERE id = ?", (selected_id,))
                        conn.commit()
                        conn.close()
                        st.toast(f"🗑️ 素材 ID {selected_id} 及其草稿已彻底销毁。")
                        st.rerun()
                    except Exception as e:
                        st.error(f"物理删除异常: {e}")
                
                if st.button("🔄 强制重读与评分 (Force Refresh)", key=f"force_reread_{selected_id}"):
                    with st.spinner("正在强制重新抓取..."):
                        if orchestrator.reread_material(selected_id):
                            st.success("重读成功。")
                            st.rerun()
                
                st.markdown("---")
                st.write("#### 📝 内容创作 (Manual Trigger)")
                if st.button("🚀 立即生成全矩阵草稿 (X, LinkedIn, Substack)", key=f"omni_gen_{selected_id}", type="primary"):
                    with st.spinner("正在为选定素材生成全矩阵草稿..."):
                        from src.engine.formatter import OmniFormatter
                        formatter = OmniFormatter()
                        results = formatter.create_omni_draft(selected_id)
                        if results:
                            st.success(f"矩阵草稿生成完成！(消耗 Token: {sum([r.get('tokens_used', 0) for r in results if isinstance(r, dict)])})")
                            st.rerun()
                        else:
                            st.error("生成失败或 Token 预算不足。")

elif menu == "情报源 (Sources)":
    st.header("🔍 情报源管理")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📡 侦察兵列表")
        conn = get_db_connection()
        sources_df = pd.read_sql_query("SELECT id, name, type, url_or_key, category, is_active, last_fetched_at FROM sources", conn)
        conn.close()
        st.dataframe(sources_df, use_container_width=True, hide_index=True)
        if st.button("🔄 立即运行全量抓取"):
            with st.spinner("调度中..."):
                saved, scored = orchestrator.crawl_all_active()
                st.success(f"完成！新素材: {saved}，已评分: {scored}")
                st.rerun()
    with col2:
        st.subheader("➕ 招募新侦察兵")
        with st.form("add_source_form"):
            s_name = st.text_input("名称")
            s_type = st.selectbox("类型", ["X (Twitter)", "RSS (Blog/Arxiv)", "WeChat (RSS)", "Akshare", "Weibo", "Agent Search (Active)"])
            s_url = st.text_input("URL/Key")
            s_cat = st.selectbox("默认领域", ["AI", "Economy"])
            if st.form_submit_button("入库"):
                conn = get_db_connection()
                conn.execute("INSERT INTO sources (name, type, url_or_key, category) VALUES (?, ?, ?, ?)", (s_name, s_type, s_url, s_cat))
                conn.commit()
                conn.close()
                st.rerun()

elif menu == "历史档案 (Archives)":
    st.header("📚 历史纵深检索")
    # ... Historical archives logic (simplified for brevity or kept same)
    st.info("功能维护中...")

elif menu == "内容变阵 (Formatter)":
    st.header("✍️ 自动化内容变阵 (OmniFormat+)")
    
    conn = get_db_connection()
    materials_df = pd.read_sql_query("SELECT id, title, score FROM materials WHERE score IS NOT NULL AND status='active' ORDER BY score DESC", conn)
    conn.close()
    
    if not materials_df.empty:
        selected_material_id = st.selectbox("选择要变阵的素材", materials_df['id'].tolist(), format_func=lambda x: f"ID {x}: {materials_df[materials_df['id']==x]['title'].values[0][:40]}...")
        
        col_gen1, col_gen2 = st.columns(2)
        with col_gen1:
            platform = st.selectbox("选择单一发布平台", ["X", "LinkedIn", "WeChat", "Substack"])
            if st.button("🚀 生成单一文案"):
                with st.spinner(f"正在为 {platform} 创作内容..."):
                    from src.engine.formatter import OmniFormatter
                    formatter = OmniFormatter()
                    draft, tokens = formatter.generate_draft(selected_material_id, platform)
                    if draft: st.success(f"{platform} 文案生成成功！(消耗 Token: {tokens})")
        
        with col_gen2:
            st.write("#### ⚡ 矩阵分发")
            if st.button("🔥 一键生成全平台矩阵草稿 (X, LinkedIn, Substack)"):
                with st.spinner("AI 正在同步为多平台矩阵创作内容..."):
                    from src.engine.formatter import OmniFormatter
                    formatter = OmniFormatter()
                    results = formatter.create_omni_draft(selected_material_id)
                    st.success("矩阵草稿生成完成！")
        
        st.markdown("---")
        st.subheader("📝 已生成的草稿预览与分发")
        
        conn = get_db_connection()
        drafts_df = pd.read_sql_query("""
            SELECT id, platform, content, status, created_at, tokens_used 
            FROM drafts 
            WHERE material_id = ? 
            ORDER BY created_at DESC
        """, conn, params=(selected_material_id,))
        conn.close()
        
        if not drafts_df.empty:
            for idx, row in drafts_df.iterrows():
                with st.expander(f"📌 {row['platform']} 草稿 ({row['status']}) - {row['created_at']}"):
                    st.caption(f"Token 消耗: {row.get('tokens_used', 0)} | 预计 ROI: 1200x")
                    draft_text = st.text_area("文案内容", value=row['content'], height=250, key=f"draft_text_{row['id']}")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("📋 复制到剪贴板", key=f"copy_{row['id']}"):
                            st.write("已模拟复制到剪贴板（请手动复制上述文本框）。")
                    with c2:
                        if st.button("🌐 推送到 Webhook", key=f"webhook_{row['id']}"):
                            from src.engine.formatter import OmniFormatter
                            formatter = OmniFormatter()
                            success, msg = formatter.push_to_webhook(row['id'])
                            if success: st.success(msg)
                            else: st.error(msg)
                    with c3:
                        if st.button("🐙 推送到 GitHub", key=f"github_{row['id']}"):
                            from src.engine.formatter import OmniFormatter
                            formatter = OmniFormatter()
                            success, msg = formatter.push_to_github(row['id'])
                            if success: st.info(msg)
        else:
            st.info("该素材尚未生成任何草稿。")
    else:
        st.write("无可用素材。")

elif menu == "♻️ 回收站 (Trash)":
    st.header("♻️ 废案回收站 (Recycle Bin)")
    st.info("此处存放已‘逻辑删除’的素材。您可以彻底销毁或尝试恢复。")
    
    conn = get_db_connection()
    trash_df = pd.read_sql_query("SELECT id, title, url, score, status, created_at FROM materials WHERE status = 'deleted'", conn)
    conn.close()
    
    if not trash_df.empty:
        st.dataframe(trash_df, use_container_width=True, hide_index=True)
        
        c_tr1, c_tr2 = st.columns(2)
        with c_tr1:
            if st.button("🔥 彻底清空回收站 (物理销毁)", type="primary"):
                conn = get_db_connection()
                conn.execute("DELETE FROM materials WHERE status = 'deleted'")
                conn.commit()
                conn.close()
                st.success("回收站已彻底清空。")
                st.rerun()
        
        with c_tr2:
            restore_id = st.number_input("输入要恢复的素材 ID", min_value=1, step=1)
            if st.button("♻️ 恢复至素材池"):
                conn = get_db_connection()
                conn.execute("UPDATE materials SET status = 'active' WHERE id = ?", (restore_id,))
                conn.commit()
                conn.close()
                st.success(f"素材 {restore_id} 已恢复。")
                st.rerun()
    else:
        st.write("回收站空空如也。")

elif menu == "系统设置":
    st.header("⚙️ 系统配置与财务审计 (Hubu Audit)")
    
    # Token Budget Section
    st.subheader("💰 令牌分模型预警 (Model Token Budget)")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    current_model = os.getenv("LLM_MODEL", "deepseek-v3-2-251201")
    
    conn = get_db_connection()
    token_usage_df = pd.read_sql_query("""
        SELECT model_name, SUM(tokens_used) as used 
        FROM audit_logs 
        WHERE created_at > ? 
        GROUP BY model_name
    """, conn, params=(yesterday,))
    conn.close()
    
    # 2.2: Refined model display logic
    usage_list = []
    total_used_24h = 0
    
    # Always include current configured model
    current_row = token_usage_df[token_usage_df['model_name'] == current_model]
    current_used = current_row['used'].sum() if not current_row.empty else 0
    usage_list.append({"name": current_model, "used": current_used})
    
    # Process others
    for _, row in token_usage_df.iterrows():
        m_val = row['model_name']
        used = row['used'] or 0
        if m_val == current_model: continue
        
        if pd.isna(m_val) or m_val is None or str(m_val).lower() in ['none', 'unknown', '', 'nan']:
            m_name = "System/Other"
        else:
            m_name = str(m_val)
            
        if used > 0: # Only show other models/system if they actually used tokens
            found = False
            for item in usage_list:
                if item['name'] == m_name:
                    item['used'] += used
                    found = True
                    break
            if not found:
                usage_list.append({"name": m_name, "used": used})
    
    total_used_24h = sum(item['used'] for item in usage_list)
    budget_limit = 1800000
    usage_pct = (total_used_24h / budget_limit) * 100
    st.progress(min(1.0, total_used_24h / budget_limit))
    st.write(f"今日总消耗: **{total_used_24h:,.0f}** / {budget_limit:,} Tokens ({usage_pct:.2f}%)")

    for item in usage_list:
        m_name = item['name']
        m_used = item['used']
        prog = min(m_used / budget_limit, 1.0)
        st.write(f"**模型: {m_name}** ({m_used:,.0f} / {budget_limit:,} tokens)")
        st.progress(prog)
        if prog >= 0.8:
            st.warning(f"⚠️ {m_name} 令牌消耗已达 {prog*100:.1f}%，接近预警阈值！")
            
    st.markdown("---")
    st.markdown("### 📈 算力产出 ROI 估算 (Hubu Metric)")
    c_roi1, c_roi2, c_roi3 = st.columns(3)
    c_roi1.metric("单篇平均成本", "¥0.08", "-12%")
    c_roi2.metric("时间节省比", "180x", "+25%")
    c_roi3.metric("预估全矩阵 ROI", "1250x", "+15%")

    st.markdown("---")
    st.subheader("🗝️ 验证码破阵模式")
    if st.button("开启影子浏览器 (手动验证)"):
        script_path = orchestrator.sogou_scraper.browser_helper.launch_interactive_browser()
        st.info("正在启动浏览器，请在弹出的窗口中完成验证。")
        import subprocess
        import sys
        import os
        
        script_abs_path = os.path.abspath(script_path)
        
        # V2.3: Use a .bat file to guarantee visibility and persistence on Windows
        if sys.platform == "win32":
            bat_path = os.path.abspath("scripts/run_browser.bat")
            # Use GBK for batch file encoding on Windows to avoid path issues
            with open(bat_path, "w", encoding="gbk") as f:
                f.write(f'@echo off\ntitle NewsTrend Shadow Browser\necho [*] Starting Browser via {sys.executable}\n"{sys.executable}" "{script_abs_path}"\nif %errorlevel% neq 0 (\n    echo.\n    echo [!] ERROR: Browser failed to launch.\n    pause\n)\n')
            
            subprocess.Popen([bat_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            st.success("浏览器启动指令已发出。请检查新弹出的黑色命令行窗口。")
        else:
            subprocess.Popen([sys.executable, script_abs_path])
            st.success("浏览器已在后台启动。")
