import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components  #Added to embed the long-term Grafana historical dashboard via an iframe
from GO_NOGOAccelerator import load_jtl_report, generate_summary, generate_recommendations

# Added client configuration dictionary to disable default file tree listing
st.set_page_config(
    page_title="Performance Release Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling to mimic the warm branding headers seen in the reference dashboard
st.markdown("""
    <style>
    /* Hides the auto-generated multi-page navigation links natively */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    .dashboard-header {
        background: linear-gradient(90deg, #FFF1E6 0%, #FF8A3D 100%);
        padding: 24px;
        border-radius: 8px;
        margin-bottom: 25px;
    }
    .main-title { color: #1E293B; margin: 0; font-weight: 800; font-style: italic; }
    .subtitle { color: #475569; margin: 5px 0 0 0; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# 1. Dashboard Masthead Row
st.markdown("""
    <div class="dashboard-header">
        <h1 class="main-title">Release Go/No-Go Dashboard</h1>
        <p class="subtitle">Monitor Performance QA Metrics & AI-Based Release Readiness</p>
    </div>
""", unsafe_allow_html=True)

# 2. File Ingestion Configuration Sidebar
st.sidebar.header("Configuration Panel")
uploaded_file = st.sidebar.file_uploader("Upload JMeter JTL / CSV Report", type=["csv", "jtl"])

# ==============================================================================
# 📉 ✨ HISTORICAL AUDIT ANALYTICS VIEW SIDEBAR INPUT
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.subheader("📉 Historical Audit Analytics View")
full_dashboard_url = st.sidebar.text_input(
    "Full Grafana Dashboard Share URL",
    value="",
    placeholder="e.g., http://localhost:3000/d/jm_metrics/jmeter-historical-run"
)

if uploaded_file is not None:
    try:
        # Load logic file parsing pipelines
        df = load_jtl_report(uploaded_file)
        summary = generate_summary(df)

        # --- Metrics Row Matrix Layout ---
        st.subheader("📊 Execution Performance Profile Summary")

        metrics_grid = pd.DataFrame([{
            "Total Sample Streams": f"{summary['total_requests']:,}",
            "Throughput Yield": f"{summary['throughput_tps']} TPS",
            "Mean Response Latency": f"{summary['mean_response_time']} ms",
            "95th Percentile": f"{summary['p95_response_time']} ms",
            "99th Percentile": f"{summary['p99_response_time']} ms",
            "Calculated Failure Rate": f"{summary['error_rate']}%"
        }])
        st.table(metrics_grid)
        st.write("---")

        # --- ✨Expanded Section Navigation Tabs to include Grafana ---
        tab_charts, tab_grafana, tab_ai = st.tabs(["📈 Charts", "📊 Deep-Dive Grafana Historicals", "🤖 AI Suggestions"])

        with tab_charts:
            left_col, right_col = st.columns(2)

            with left_col:
                st.markdown("#### Overall Release Score Gauge")
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=summary['release_score'],
                    title={'text': f"Verdict Status: {summary['status']}", 'font': {'size': 14}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#10B981" if summary['release_score'] >= 80 else "#EF4444"},
                        'steps': [
                            {'range': [0, 50], 'color': '#FEE2E2'},
                            {'range': [50, 80], 'color': '#FEF3C7'},
                            {'range': [80, 100], 'color': '#D1FAE5'}
                        ],
                    }
                ))
                fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

            with right_col:
                st.markdown("#### Latency Tier Distributions")
                fig_bar = go.Figure(data=[
                    go.Bar(
                        x=['Mean', '95th %ile', '99th %ile', 'Max Latency'],
                        y=[summary['mean_response_time'], summary['p95_response_time'], summary['p99_response_time'],
                           summary['max_response_time']],
                        marker_color='#FF8A3D'
                    )
                ])
                fig_bar.update_layout(height=280, yaxis_title="Time (ms)", margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_bar, use_container_width=True)

        # ==============================================================================
        # 📊 ✨ RENDER NEW FULL HISTORICAL DEEP-DIVE GRAFANA TAB
        # ==============================================================================
        with tab_grafana:
            st.markdown("#### Deep-Dive Hardware Infrastructure & Load Evaluation Workspace")
            if full_dashboard_url:
                components.iframe(full_dashboard_url, height=750, scrolling=True)
            else:
                st.info("ℹ️ Paste a shared dashboard URL inside the sidebar option array to visualize long-term performance trend lines.")

        with tab_ai:
            st.markdown("#### Automated Remediation Strategy Advice")
            with st.spinner("Processing performance telemetry profiles..."):
                ai_insights = generate_recommendations(summary)
                st.markdown(ai_insights)

    except Exception as e:
        st.error(f"Application Execution Error: {e}")
else:
    st.info(
        "💡 Drop an executed JMeter test run file (`.jtl` or `.csv`) into the sidebar utility pane to automatically build the scorecard matrix layout.")