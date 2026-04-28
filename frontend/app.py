"""
DataMind — AI-Powered Data Analysis Dashboard
----------------------------------------------
A professional Streamlit dashboard that makes data analysis
feel like talking to a senior data analyst.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.io as pio
import json
import uuid

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS — Notion-style clean light theme ───────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #f9f9f7; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e8e8e4;
    }

    /* Cards */
    .metric-card {
        background: white;
        border: 1px solid #e8e8e4;
        border-radius: 8px;
        padding: 20px;
        margin: 8px 0;
    }

    /* Insight cards */
    .insight-card {
        background: white;
        border-left: 3px solid #6366f1;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
        color: #333;
    }

    /* Anomaly cards */
    .anomaly-card {
        background: #fff8f0;
        border-left: 3px solid #f59e0b;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
    }

    /* Chat messages */
    .user-message {
        background: #6366f1;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        font-size: 14px;
    }

    .ai-message {
        background: white;
        border: 1px solid #e8e8e4;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 85%;
        font-size: 14px;
        color: #333;
    }

    /* Follow-up chips */
    .followup-chip {
        display: inline-block;
        background: #f0f0ff;
        border: 1px solid #c7d2fe;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 4px;
        font-size: 12px;
        color: #6366f1;
        cursor: pointer;
    }

    /* Quality score */
    .quality-score {
        font-size: 48px;
        font-weight: bold;
        color: #6366f1;
        text-align: center;
    }

    /* Section headers */
    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #1a1a2e;
        margin: 20px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #e8e8e4;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

API = "http://localhost:8000"

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "session_id"  not in st.session_state:
    st.session_state.session_id  = str(uuid.uuid4())[:8]
if "uploaded"    not in st.session_state:
    st.session_state.uploaded    = False
if "filename"    not in st.session_state:
    st.session_state.filename    = None
if "analysis"    not in st.session_state:
    st.session_state.analysis    = None
if "chat"        not in st.session_state:
    st.session_state.chat        = []
if "df_preview"  not in st.session_state:
    st.session_state.df_preview  = None


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 DataMind")
    st.markdown("*AI-Powered Data Analyst*")
    st.divider()

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload your data",
        type=["csv", "xlsx", "xls"],
        help="Supports CSV and Excel files"
    )

    if uploaded_file:
        if uploaded_file.name != st.session_state.filename:
            with st.spinner("Uploading..."):
                try:
                    response = requests.post(
                        f"{API}/upload/{st.session_state.session_id}",
                        files={"file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.uploaded  = True
                        st.session_state.filename  = uploaded_file.name
                        st.session_state.analysis  = None
                        st.session_state.chat      = []
                        st.session_state.df_preview = None
                        st.success(f"✅ {data['rows']:,} rows × {data['columns']} columns")
                    else:
                        st.error("Upload failed")
                except Exception as e:
                    st.error(f"Backend not running: {e}")

    if st.session_state.uploaded:
        st.markdown(f"**📄 {st.session_state.filename}**")
        st.divider()

        # Run analysis button
        if st.button("🔍 Run AI Analysis", type="primary", use_container_width=True):
            with st.spinner("Analysing your data with AI... ⚡"):
                try:
                    r = requests.get(
                        f"{API}/analyse/{st.session_state.session_id}"
                    )
                    st.session_state.analysis = r.json()
                    st.success("Analysis complete!")
                except Exception as e:
                    st.error(str(e))

        # Export PDF
        if st.session_state.analysis:
            if st.button("📥 Export PDF Report", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    try:
                        r = requests.post(
                            f"{API}/export/{st.session_state.session_id}"
                        )
                        st.download_button(
                            "⬇️ Download Report",
                            data=r.content,
                            file_name="datamind_report.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(str(e))

        st.divider()

        # Clear session
        if st.button("🗑️ Clear", use_container_width=True):
            try:
                requests.delete(
                    f"{API}/session/{st.session_state.session_id}"
                )
            except Exception:
                pass
            for key in ["uploaded", "filename", "analysis", "chat", "df_preview"]:
                st.session_state[key] = None if key != "chat" else []
            st.session_state.uploaded = False
            st.session_state.session_id = str(uuid.uuid4())[:8]
            st.rerun()

    st.divider()
    st.caption("Built with FastAPI · Gemini · Plotly · Streamlit")
    st.caption(f"Session: `{st.session_state.session_id}`")


# ── MAIN CONTENT ──────────────────────────────────────────────────────────────

# Welcome screen
if not st.session_state.uploaded:
    st.markdown("""
    <div style='text-align: center; padding: 80px 20px;'>
        <div style='font-size: 64px;'>🧠</div>
        <h1 style='color: #1a1a2e; font-size: 42px; margin: 16px 0;'>DataMind</h1>
        <p style='color: #666; font-size: 18px; max-width: 500px; margin: 0 auto;'>
            Upload any CSV or Excel file and get instant AI-powered insights,
            interactive charts, anomaly detection, and natural language Q&A.
        </p>
        <br/>
        <p style='color: #999; font-size: 14px;'>
            ← Upload your file in the sidebar to get started
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Analysis & Insights",
        "💬 Ask AI",
        "🔢 Data Preview",
        "⚠️ Anomalies"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — ANALYSIS & INSIGHTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        if not st.session_state.analysis:
            st.info(
                "👈 Click **Run AI Analysis** in the sidebar to generate "
                "insights, charts, and data quality report."
            )
        else:
            analysis = st.session_state.analysis
            insights = analysis.get("insights", {})
            profile  = analysis.get("profile", {})

            # ── Dataset description ────────────────────────────────────────────
            st.markdown(
                f"<div class='section-header'>📋 Dataset Overview</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div class='ai-message'>{insights.get('dataset_description', '')}</div>",
                unsafe_allow_html=True
            )

            # ── Metrics row ────────────────────────────────────────────────────
            shape = profile.get("shape", {})
            missing = sum(profile.get("missing_values", {}).values())
            dq_score = insights.get("data_quality", {}).get("score", 0)

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("📦 Total Rows",    f"{shape.get('rows', 0):,}")
            with m2:
                st.metric("📐 Columns",       shape.get("columns", 0))
            with m3:
                st.metric("❓ Missing Values", missing)
            with m4:
                st.metric("✨ Quality Score",  f"{dq_score}/100")

            st.divider()

            # ── Key insights ───────────────────────────────────────────────────
            st.markdown(
                "<div class='section-header'>💡 Key AI Insights</div>",
                unsafe_allow_html=True
            )
            for insight in insights.get("key_insights", []):
                st.markdown(
                    f"<div class='insight-card'>💡 {insight}</div>",
                    unsafe_allow_html=True
                )

            st.divider()

            # ── Charts ─────────────────────────────────────────────────────────
            st.markdown(
                "<div class='section-header'>📈 Auto-Generated Charts</div>",
                unsafe_allow_html=True
            )
            charts = analysis.get("charts", [])
            if charts:
                # Display charts in pairs
                for i in range(0, len(charts), 2):
                    cols = st.columns(2)
                    for j, col in enumerate(cols):
                        if i + j < len(charts):
                            chart = charts[i + j]
                            with col:
                                try:
                                    fig = pio.from_json(chart["json"])
                                    st.plotly_chart(
                                        fig,
                                        use_container_width=True,
                                        key=f"chart_{i}_{j}"
                                    )
                                except Exception:
                                    st.warning(f"Could not render: {chart['title']}")

            st.divider()

            # ── Business implications ──────────────────────────────────────────
            st.markdown(
                "<div class='section-header'>💼 Business Implications</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div class='ai-message'>{insights.get('business_implications', '')}</div>",
                unsafe_allow_html=True
            )

            # ── Recommended analyses ───────────────────────────────────────────
            st.divider()
            st.markdown(
                "<div class='section-header'>🎯 Recommended Analyses</div>",
                unsafe_allow_html=True
            )
            recs = insights.get("recommended_analyses", [])
            if recs:
                cols = st.columns(min(len(recs), 3))
                for i, rec in enumerate(recs[:3]):
                    with cols[i]:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <strong>{rec['title']}</strong><br/>
                            <span style='color:#666; font-size:13px;'>
                                {rec['description']}
                            </span><br/><br/>
                            <span style='background:#f0f0ff; color:#6366f1;
                                padding:2px 8px; border-radius:10px;
                                font-size:12px;'>
                                {rec.get('chart_type', 'chart')}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — AI CHAT
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown(
            "<div class='section-header'>💬 Ask AI about your data</div>",
            unsafe_allow_html=True
        )
        st.caption(
            "Ask anything in plain English — AI will answer and "
            "generate a chart if relevant."
        )

        # Suggested questions
        if st.session_state.analysis and not st.session_state.chat:
            questions = st.session_state.analysis.get(
                "insights", {}
            ).get("interesting_questions", [])

            if questions:
                st.markdown("**💡 Suggested questions:**")
                cols = st.columns(min(len(questions), 3))
                for i, q in enumerate(questions[:3]):
                    with cols[i]:
                        if st.button(q, key=f"sq_{i}", use_container_width=True):
                            st.session_state.chat.append({
                                "role": "user", "content": q
                            })
                            st.rerun()

        # Chat history
        for i, msg in enumerate(st.session_state.chat):
            if msg["role"] == "user":
                st.markdown(
                    f"<div class='user-message'>{msg['content']}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div class='ai-message'>{msg['content']}</div>",
                    unsafe_allow_html=True
                )
                if msg.get("chart"):
                    try:
                        fig = pio.from_json(msg["chart"])
                        st.plotly_chart(
                            fig, use_container_width=True, key=f"chat_chart_{i}"
                        )
                    except Exception:
                        pass
                if msg.get("follow_up"):
                    st.markdown("**Ask next:**")
                    fu_cols = st.columns(min(len(msg["follow_up"]), 2))
                    for j, fq in enumerate(msg["follow_up"][:2]):
                        with fu_cols[j]:
                            if st.button(
                                fq, key=f"fu_{i}_{j}",
                                use_container_width=True
                            ):
                                st.session_state.chat.append({
                                    "role": "user", "content": fq
                                })
                                st.rerun()

        # Process pending user message
        last = st.session_state.chat[-1] if st.session_state.chat else None
        if last and last["role"] == "user" and not any(
            m["role"] == "assistant" and
            st.session_state.chat.index(m) >
            st.session_state.chat.index(last)
            for m in st.session_state.chat
            if m["role"] == "assistant"
        ):
            # Find if this user message has been answered
            idx = len(st.session_state.chat) - 1
            if idx == 0 or st.session_state.chat[idx - 1]["role"] == "assistant":
                with st.spinner("Thinking..."):
                    try:
                        r = requests.post(
                            f"{API}/ask/{st.session_state.session_id}",
                            json={"question": last["content"]}
                        )
                        data = r.json()
                        st.session_state.chat.append({
                            "role":      "assistant",
                            "content":   data.get("answer", ""),
                            "chart":     data.get("chart"),
                            "follow_up": data.get("follow_up", []),
                        })
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

        # Input box
        st.divider()
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                question = st.text_input(
                    "Ask a question",
                    placeholder="e.g. What is the average price by neighbourhood?",
                    label_visibility="collapsed"
                )
            with col2:
                submitted = st.form_submit_button(
                    "Send →", use_container_width=True
                )

        if submitted and question.strip():
            st.session_state.chat.append({
                "role": "user", "content": question
            })
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — DATA PREVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown(
            "<div class='section-header'>🔢 Data Preview</div>",
            unsafe_allow_html=True
        )

        if not st.session_state.df_preview:
            with st.spinner("Loading data..."):
                try:
                    r = requests.get(
                        f"{API}/preview/{st.session_state.session_id}?rows=100"
                    )
                    st.session_state.df_preview = r.json()
                except Exception as e:
                    st.error(str(e))

        if st.session_state.df_preview:
            preview = st.session_state.df_preview
            st.caption(
                f"Showing first 100 of {preview['total_rows']:,} rows"
            )
            df = pd.DataFrame(preview["data"])
            st.dataframe(
                df,
                use_container_width=True,
                height=500,
            )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — ANOMALIES
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown(
            "<div class='section-header'>⚠️ Anomaly Detection</div>",
            unsafe_allow_html=True
        )
        st.caption(
            "Automatically detected outliers using the IQR method. "
            "These may indicate data errors, fraud, or genuine extremes."
        )

        if not st.session_state.analysis:
            st.info("Run AI Analysis first to detect anomalies.")
        else:
            anomalies = st.session_state.analysis.get("anomalies", [])
            if not anomalies:
                st.success("✅ No significant anomalies detected.")
            else:
                for a in anomalies:
                    pct = a["outlier_pct"]
                    color = "#ef4444" if pct > 10 else "#f59e0b"
                    st.markdown(f"""
                    <div class='anomaly-card'>
                        <strong style='color:{color};'>
                            ⚠ {a['column']}
                        </strong>
                        &nbsp;&nbsp;
                        <span style='background:{color}20; color:{color};
                            padding:2px 8px; border-radius:10px; font-size:12px;'>
                            {a['outlier_count']} outliers ({pct}%)
                        </span>
                        <br/>
                        <span style='color:#666; font-size:13px;'>
                            Expected range: {a['lower_bound']} to {a['upper_bound']}
                            &nbsp;|&nbsp;
                            Found values as low as {a['min_outlier']}
                            and as high as {a['max_outlier']}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                # Data quality from insights
                if st.session_state.analysis.get("insights"):
                    dq = st.session_state.analysis["insights"].get(
                        "data_quality", {}
                    )
                    st.divider()
                    st.markdown(
                        "<div class='section-header'>📋 Data Quality Report</div>",
                        unsafe_allow_html=True
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Issues found:**")
                        for issue in dq.get("issues", []):
                            st.markdown(f"⚠️ {issue}")
                    with c2:
                        st.markdown("**Strengths:**")
                        for s in dq.get("strengths", []):
                            st.markdown(f"✅ {s}")