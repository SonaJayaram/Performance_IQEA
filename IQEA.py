import streamlit as st
import sys
import os

st.set_page_config(page_title="IQEA Platform", layout="wide")

st.markdown("""
<style>

/* ===== HIDE AUTO-GENERATED STREAMLIT NAV ===== */
[data-testid="stSidebarNav"] {
    display: none !important;
}

[data-testid="stAppViewContainer"] {
    background-color: #f4f6f9;
    font-family: 'Segoe UI', sans-serif;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #F47B20, #F47B20);
    padding-top: 0px;
}

[data-testid="stSidebar"] * { color: white !important; }

/* ===== FIX RADIO ALIGNMENT ===== */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    margin-bottom: 4px !important;
    cursor: pointer !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label div:first-child {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    align-self: center !important;
    flex-shrink: 0 !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
    align-self: center !important;
}

.card {
    background-color: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.06);
    margin-bottom: 20px;
}
.section-title { font-size: 20px; font-weight: 600; margin-bottom: 10px; }
/* ===== FIX LAYOUT SHIFT ===== */
.block-container {
    padding: 2rem 3rem !important;
    min-height: 100vh !important;
    width: 100% !important;
    max-width: 100% !important;
}

[data-testid="stMainBlockContainer"] {
    min-height: 100vh !important;
    width: 100% !important;
    max-width: 100% !important;
}

[data-testid="column"] {
    width: 100% !important;
    min-width: 0 !important;
    flex: 1 1 0% !important;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# BASE PATH
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_page(file_path):
    """Run a page file with its own directory as working directory."""
    page_dir = os.path.dirname(file_path)
    if page_dir not in sys.path:
        sys.path.insert(0, page_dir)
    original_dir = os.getcwd()
    os.chdir(page_dir)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            exec(f.read(), {"__file__": file_path})
    finally:
        os.chdir(original_dir)

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    img_base64 = __import__('base64').b64encode(
        open(r"C:\Users\sathanantham.aru\Downloads\IQEA.ai.png", "rb").read()
    ).decode()

    st.markdown(f"""
    <style>
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}
    [data-testid="stSidebarContent"] {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}
    section[data-testid="stSidebar"] > div {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}
    [data-testid="stSidebar"] div:first-child {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}
    </style>
    <div style="margin:0 !important; padding:0 !important; text-align:center;">
        <img src="data:image/png;base64,{img_base64}"
             style="width:150px; margin:0; padding:0; display:block; margin-left:auto; margin-right:auto;" />
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### QE Agentic E2E Solutions")
    st.markdown("---")

    page = st.radio(
        "Go to",
        ["🏠 Home", "🧠 IQEA", "🔁 Self Healing", "🔗 API","Performance Testing"],
        index=0,
        label_visibility="collapsed"
    )

# ==============================
# PAGE ROUTING
# ==============================
if page == "🏠 Home":
    st.title("🤖 TigerQE AI Platform - iQEA")
    st.markdown("""
    <div class="card">
        <div class="section-title">🚀 IQEA - End to End Automation Platform</div>
        <ul>
            <li>Low-code / No-code E2E test artefacts generation</li>
            <li>AI-augmented test case & automation code generation</li>
            <li>Data-driven decisions (~30% efficiency gain)</li>
            <li>AI-powered self-healing for UI changes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="card">
            <div class="section-title">🔁 Web Self Healing</div>
            <p>Maintain large regression suites efficiently using AI-driven healing.</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
            <div class="section-title">🔗 API Automation</div>
            <p>Seamless API testing with integrated performance testing.</p>
        </div>""", unsafe_allow_html=True)

elif page == "🧠 IQEA":
    run_page(os.path.join(BASE_DIR, "action_new_xpath_subway.py"))

elif page == "🔁 Self Healing":
    run_page(os.path.join(BASE_DIR, "Self_healing_web_application", "Self_healing_streamlet.py"))

elif page == "🔗 API":
    run_page(os.path.join(BASE_DIR, "api_validator.py"))
elif page == "Performance Testing":
    run_page(os.path.join(BASE_DIR, "action_new_xpath_performance.py"))