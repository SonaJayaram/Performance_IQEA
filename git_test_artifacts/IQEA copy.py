import streamlit as st
import sys
import os

st.set_page_config(page_title="IQEA Platform", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>

/* ===== HIDE STREAMLIT CHROME ===== */
[data-testid="stSidebarNav"]            { display: none !important; }
[data-testid="stHeader"]                { display: none !important; }
[data-testid="stToolbar"]               { display: none !important; }
[data-testid="stDecoration"]            { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="collapsedControl"]        { display: none !important; }
[data-testid="stSidebarResizeHandle"]   { display: none !important; }
#MainMenu                               { display: none !important; }
footer                                  { display: none !important; }

/* ===== APP BACKGROUND ===== */
[data-testid="stAppViewContainer"] {
    background-color: #F0F2F6;
    font-family: 'Segoe UI', sans-serif;
}

# /* ===== SIDEBAR BASE ===== */
# [data-testid="stSidebar"] {
#     background: linear-gradient(180deg, #E8650A 0%, #F47B20 60%, #F99245 100%);
#     padding-top: 0px;
# }

# /* All sidebar text → white */
# [data-testid="stSidebar"] * {
#     color: white !important;
#     font-weight: 700 !important;
# }
/* ===== SIDEBAR BASE ===== */
[data-testid="stSidebar"] {
    /* REMOVE the old gradient here — it's now handled inline above */
    padding-top: 0px;
}

/* Keep all sidebar text white EXCEPT the title zone */
[data-testid="stSidebar"] * {
    color: white !important;
    font-weight: 700 !important;
}

/* Override: title text must be black (white zone) */
[data-testid="stSidebar"] h3 {
    color: #000000 !important;;
}
/* ===== SIDEBAR SECTION HEADER ===== */
[data-testid="stSidebar"] h3 {
    font-size: 22px !important;
    font-weight: 800 !important;
    color: #000000 !important;;
    text-align: center !important;
    letter-spacing: 0.5px !important;
}

/* ===== NAV RADIO LABELS ===== */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 14px 18px !important;
    border-radius: 10px !important;
    margin-bottom: 8px !important;
    cursor: pointer !important;
    border-left: 4px solid transparent !important;
    transition: background 0.2s !important;
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
    font-size: 20px !important;
    font-weight: 700 !important;
    color: white !important;
    line-height: 1.2 !important;
    align-self: center !important;
}

/* ===== SELECTED NAV ITEM ===== */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
    background-color: white !important;
    border-left: 4px solid #E8650A !important;
    border-radius: 10px !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) p {
    color: #E8650A !important;
    font-weight: 800 !important;
    font-size: 20px !important;
}

/* ===== LAYOUT ===== */
.block-container {
    padding: 0rem 2rem 2rem 2rem !important;
    max-width: 100% !important;
}

[data-testid="stMainBlockContainer"] {
    max-width: 100% !important;
}

[data-testid="column"] {
    width: 100% !important;
    min-width: 0 !important;
    flex: 1 1 0% !important;
}

/* ===== TEXT INPUTS & TEXT AREAS ===== */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #ffffff !important;
    border: 2px solid #C8CDD6 !important;
    border-radius: 8px !important;
    color: #1B2A4A !important;
    font-size: 15px !important;
    padding: 8px 12px !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border: 2px solid #F47B20 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(244, 123, 32, 0.15) !important;
}

[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #A0A8B4 !important;
    font-weight: 400 !important;
}

/* ===== SELECTBOX & MULTISELECT ===== */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background-color: #ffffff !important;
    border: 2px solid #C8CDD6 !important;
    border-radius: 8px !important;
}

[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stMultiSelect"] > div > div:focus-within {
    border: 2px solid #F47B20 !important;
    box-shadow: 0 0 0 3px rgba(244, 123, 32, 0.15) !important;
}

[data-testid="stSelectbox"] span,
[data-testid="stMultiSelect"] span {
    color: #1B2A4A !important;
    font-weight: 500 !important;
}

/* dropdown menu list */
[data-baseweb="popover"] ul {
    background-color: #ffffff !important;
    border: 1px solid #C8CDD6 !important;
    border-radius: 8px !important;
}

[data-baseweb="popover"] li {
    color: #1B2A4A !important;
    font-size: 15px !important;
}

[data-baseweb="popover"] li:hover {
    background-color: #FFF0E6 !important;
    color: #F47B20 !important;
}

/* ===== HOME PAGE STYLES ===== */
.feature-card {
    background: white;
    border-radius: 14px;
    border-top: 5px solid #F47B20;
    padding: 28px 24px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    height: 100%;
}
.feature-card-title {
    font-size: 22px;
    font-weight: 800;
    color: #F47B20;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.feature-card li {
    font-size: 15px;
    line-height: 1.9;
    color: #2C2C2C;
    margin-bottom: 2px;
}
.feature-card ul {
    padding-left: 18px;
    margin: 0;
}
.feature-card li::marker {
    color: #F47B20;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# BASE PATH
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_page(file_path):
    """Run a page file in-place without changing the process CWD."""
    page_dir = os.path.dirname(file_path)
    if page_dir not in sys.path:
        sys.path.insert(0, page_dir)
    # NOTE: We deliberately do NOT evict cached submodules from sys.modules here.
    # An earlier version evicted every module whose __file__ lived under the
    # project root to hot-reload edits to utils/*.py without a restart. That was
    # harmful:
    #   * The virtualenv (.venv) sits inside the project root, so it also evicted
    #     Streamlit's own modules -> re-import mid-run with fresh ContextVars ->
    #     "FragmentThreadState not initialized" and pages failing to load.
    #   * Even limited to the app's own modules, it forced heavy re-imports of
    #     desktop.recorder etc. (native keyboard/mouse hooks, pywinauto) on every
    #     navigation, which intermittently hung or crashed the server.
    # Modules are now imported once and cached. If you edit utils/*.py during
    # development, restart the Streamlit server to pick up the changes.
    with open(file_path, "r", encoding="utf-8") as f:
        exec(f.read(), {"__file__": file_path})

# ==============================
# SIDEBAR
# ==============================
# with st.sidebar:
#     img_base64 = __import__('base64').b64encode(
#         open("utilities/IQEA.ai_logo.png", "rb").read()
#     ).decode()

#     st.markdown(f"""
#     <style>
#     [data-testid="stSidebar"] > div:first-child,
#     [data-testid="stSidebarContent"],
#     section[data-testid="stSidebar"] > div,
#     [data-testid="stSidebar"] div:first-child {{
#         padding-top: 0 !important;
#         margin-top: 0 !important;
#     }}
#     </style>
#     <div style="background-color:white; padding:16px 12px 10px 12px; text-align:center;
#                 border-bottom: 3px solid rgba(255,255,255,0.4);">
#         <img src="data:image/png;base64,{img_base64}"
#              style="width:155px; display:block; margin:0 auto;" />
#     </div>
#     """, unsafe_allow_html=True)

#     st.markdown("<br>", unsafe_allow_html=True)
#     st.markdown("### QE Agentic E2E Solutions")
#     st.markdown("<hr style='border:1px solid rgba(255,255,255,0.4); margin:8px 0 16px 0;'>",
#                 unsafe_allow_html=True)

#     page = st.radio(
#         "Go to",
#         ["🏠  Home", "🧠  IQEA", "🔁  Self Healing", "🔗  API Validator"],
#         index=0,
#         label_visibility="collapsed"
#     )
# Replace the existing sidebar logo + markdown block with this:

with st.sidebar:
    img_base64 = __import__('base64').b64encode(
        open("utilities/IQEA.ai_logo.png", "rb").read()
    ).decode()

    st.markdown(f"""
    <style>
    /* Remove all top padding from sidebar */
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] div:first-child {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}

    /* Override sidebar gradient — start white, transition to orange */
    [data-testid="stSidebar"] {{
        background: linear-gradient(
            180deg,
            #FFFFFF 0%,
            #FFFFFF 46%,    /* ← increase this until divider is in white zone */
            #E8650A 46%,    /* ← match this to the same value */
            #F47B20 60%,
            #F99245 100%
        ) !important;
    }}

    /* Title text in the white zone must be black */
    # [data-testid="stSidebar"] h3 {{
    #     color: #1B2A4A !important;
    #     font-size: 20px !important;
    #     font-weight: 800 !important;
    #     text-align: center !important;
    #     letter-spacing: 0.5px !important;
    # }}

    # /* Divider line below title — dark instead of white */
    # .sidebar-divider {{
    #     border: 1px solid #D0D0D0;
    #     margin: 8px 0 16px 0;
    # }}
    [data-testid="stSidebar"] h3 {{
        color: #000000 !important;;
        font-size: 20px !important;
        font-weight: 800 !important;
        text-align: center !important;
    }}

    /* Divider line — dark grey to match white background */
    .sidebar-divider {{
        border: 1px solid #D0D0D0 !important;
        margin: 8px 0 16px 0;
    }}

    /* Prevent the global white override from recoloring the title */
    [data-testid="stSidebar"] h3 {{
        color: #000000 !important;
    }}            
    </style>

    <div style="
        background-color: white;
        padding: 20px 12px 16px 12px;
        text-align: center;
    ">
        <img src="data:image/png;base64,{img_base64}"
            style="width: 155px; display: block; margin: 0 auto;" />
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### QE Agentic E2E Solutions")
    st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

    page = st.radio(
        "Go to",
        ["🏠  Home", "🧠  IQEA", "🔁  Self Healing", "🔗  API Validator", "📊  PBI Validator"],
        index=0,
        label_visibility="collapsed"
    )
# ==============================
# PAGE ROUTING
# ==============================
if page == "🏠  Home":
    st.markdown("""
    <div style="padding: 28px 0 24px 0;">
        <div style="font-size:34px; font-weight:900; color:#1B2A4A; margin-bottom:8px;">
            🤖 TigerQE AI Platform — iQEA (Intelligent QE Assistant)
        </div>
        <div style="font-size:17px; color:#666; font-weight:500;">
            AI-powered end-to-end test automation — from recording to execution, all in one place.
        </div>
        <hr style="border:2px solid #F47B20; width:80px; margin:16px 0 0 0;">
    </div>
    """, unsafe_allow_html=True)

    # col1, col2, col3 = st.columns(3, gap="large")
    # with col1:
    
    st.markdown("""
    <div class="feature-card">
        <div class="feature-card-title">Key Features</div>        
        <ul class="feature-list">
            <li>
                <span class="feat-icon">🎯</span>
                <span><strong>Test Generation from User Journey</strong> — Auto-generate test cases by recording real user workflows on web &amp; desktop, no scripting needed</span>
            </li>
            <li>
                <span class="feat-icon">🔗</span>
                <span><strong>Seamless Integration</strong> — Native sync with test management tools (Jira, Azure Boards) and source code version controllers (Git)</span>
            </li>
            <li>
                <span class="feat-icon">🔧</span>
                <span><strong>Low-Effort Test Maintenance (Self-Healing)</strong> — AI automatically detects and repairs broken locators and test steps after UI changes</span>
            </li>
            <li>
                <span class="feat-icon">🤖</span>
                <span><strong>AI-Augmented XPath &amp; Automation</strong> — Intelligent locator generation and maintenance with full Page Object Model support</span>
            </li>
            <li>
                <span class="feat-icon">⚡</span>
                <span><strong>2× Faster QE Cycle</strong> — Dramatically reduce time-to-test with one-click script generation in Java or Python</span>
            </li>
            <li>
                <span class="feat-icon">🛠️</span>
                <span><strong>Quick Customization</strong> — Flexible templates and configurations adapt to your team's standards and tech stack instantly</span>
            </li>
            <li>
                <span class="feat-icon">📋</span>
                <span><strong>Regulatory Compliance &amp; Adherence Reporting</strong> — Built-in compliance-ready reports for standards like GDPR, HIPAA &amp; ISO</span>
            </li>
            <li>
                <span class="feat-icon">🔍</span>
                <span><strong>Smarter Regression — Scan &amp; Fix Changes</strong> — Automatically identifies impacted test cases when code changes and flags fixes needed</span>
            </li>
            <li>
                <span class="feat-icon">🚀</span>
                <span><strong>Faster Regression with AIR</strong> — Artificial Impact Reviewer prioritizes and runs only the tests affected by recent changes</span>
            </li>
            <li>
                <span class="feat-icon">📊</span>
                <span><strong>Built-in Performance Benchmarking</strong> — Measure and track response times across all endpoints without leaving the platform</span>
            </li>
            <li>
                <span class="feat-icon">📄</span>
                <span><strong>Seamless Swagger Integration</strong> — Auto-generate API test cases directly from Swagger/OpenAPI specs with zero manual effort</span>
            </li>
        </ul>
    </div>
    <style>
    .feature-card {
        background: #ffffff;
        border: 2px solid #FF6B00;
        border-radius: 12px;
        padding: 24px 28px;
        height: 100%;
        box-shadow: 0 4px 20px rgba(255, 107, 0, 0.15);
    }
    .feature-card-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #FF6B00;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }
    .key-features-label {
        font-size: 0.100rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #FF6B00;
        margin-bottom: 16px;
        border-bottom: 2px solid #FF6B00;
        padding-bottom: 10px;
    }
    .feat-icon {
        font-size: 1rem;
        min-width: 22px;
        margin-top: 1px;
    }
    .feature-list li strong {
        color: #FF6B00;
    }
    </style>           
    """, unsafe_allow_html=True)
    

elif page == "🧠  IQEA":
    run_page(os.path.join(BASE_DIR, "action_new_xpath_subway_TMT.py"))

elif page == "🔁  Self Healing":
    run_page(os.path.join(BASE_DIR, "Self_healing_web_application", "Self_healing_streamlet.py"))

elif page == "🔗  API Validator":
    run_page(os.path.join(BASE_DIR, "api_validator.py"))

elif page == "📊  PBI Validator":
    run_page(os.path.join(BASE_DIR, "pbi_validator", "pbi_validator_streamlit.py"))
