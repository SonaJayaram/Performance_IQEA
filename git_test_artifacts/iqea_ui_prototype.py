"""
IQEA UI Prototype  —  new "workbench" navigation shell.

Run it standalone to feel the UX (backend not required):

    streamlit run iqea_ui_prototype.py

Goal: kill the "stack of 9 scrolling accordions" feel. Instead:
  • Left TOOL RAIL grouped by QE lifecycle phase (industry-standard app-console layout).
  • Exactly ONE tool renders at a time on the right  ->  no scroll-to-find,
    scroll only inside the focused tool.
  • Every tool is independently runnable  ->  no implied sequence.
  • API Validator redesigned as clean sub-tabs (Validation / Performance / AI Insights).

The tool bodies here are PLACEHOLDERS (representative widgets + notes) so the
prototype runs with no Selenium / Azure / DB dependencies. Once you approve the
shell, the real logic from action_new_xpath_subway_TMT.py / api_validator.py
drops straight into each render_* function.
"""

import streamlit as st

st.set_page_config(page_title="TigerQE AI — iQEA", page_icon="🤖", layout="wide")

# ----------------------------------------------------------------------------
# THEME  (matches the existing orange IQEA brand)
# ----------------------------------------------------------------------------
ORANGE = "#F47B20"
ORANGE_DK = "#E8650A"
INK = "#1B2A4A"

st.markdown(f"""
<style>
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {{ display:none !important; }}
[data-testid="stAppViewContainer"] {{ background:#F0F2F6; font-family:'Segoe UI',sans-serif; }}
.block-container {{ padding-top:1rem !important; max-width:100% !important; }}

/* ---- sticky context bar ---- */
.ctx-bar {{
    background:#fff; border:1px solid #E3E6EC; border-left:5px solid {ORANGE};
    border-radius:12px; padding:14px 20px; margin-bottom:14px;
    box-shadow:0 2px 10px rgba(0,0,0,.05);
}}
.ctx-title {{ font-size:22px; font-weight:800; color:{INK}; margin:0; }}
.ctx-sub   {{ font-size:13px; color:#7A8290; margin:0; }}

/* ---- tool rail ---- */
.rail-phase {{
    font-size:11px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase;
    color:{ORANGE_DK}; margin:16px 0 6px 4px;
}}
/* nav buttons: secondary = idle, primary = active tool */
[data-testid="stSidebar"] {{ display:none; }}   /* prototype: no global sidebar */

div[data-testid="column"]:first-child .stButton>button {{
    text-align:left; justify-content:flex-start;
    border-radius:9px; border:1px solid transparent;
    font-weight:600; padding:9px 12px; margin-bottom:3px;
}}
div[data-testid="column"]:first-child .stButton>button[kind="secondary"] {{
    background:#fff; color:{INK}; border-color:#E3E6EC;
}}
div[data-testid="column"]:first-child .stButton>button[kind="secondary"]:hover {{
    border-color:{ORANGE}; color:{ORANGE_DK};
}}
div[data-testid="column"]:first-child .stButton>button[kind="primary"] {{
    background:{ORANGE}; color:#fff; border-color:{ORANGE};
}}

/* ---- workspace card ---- */
.ws-card {{
    background:#fff; border:1px solid #E3E6EC; border-radius:14px;
    padding:26px 30px; box-shadow:0 4px 16px rgba(0,0,0,.06);
}}
.ws-head {{ font-size:24px; font-weight:800; color:{INK}; margin:0 0 2px 0; }}
.ws-desc {{ font-size:14px; color:#7A8290; margin:0 0 18px 0; }}
.rail-card {{
    background:#fff; border:1px solid #E3E6EC; border-radius:14px;
    padding:14px 12px; box-shadow:0 4px 16px rgba(0,0,0,.06);
}}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# TOOL REGISTRY  —  the 9 tools grouped by QE lifecycle phase
# ============================================================================
PHASES = [
    ("🎬 Capture", [
        ("recorder", "🔴 Workflow Recorder", "Record web/desktop user journeys and capture screenshots."),
    ]),
    ("📝 Author", [
        ("testcases", "🧮 E2E Test Case Generator", "Generate functional test cases from recordings, docs or TMT."),
        ("bdd",       "🧾 BDD Feature File Generator", "Turn recorded actions into Gherkin .feature files."),
        ("testdata",  "🧪 Test Data Generator", "Produce action-driven test data sets."),
    ]),
    ("🔧 Build", [
        ("pom",     "🔎 Locators / POM Generator", "Generate locators and Page Object Model classes."),
        ("scripts", "📜 Automation Script Generator", "Generate runnable scripts from page files + test cases."),
    ]),
    ("🚀 Run & Report", [
        ("execute",   "▶️ Test Execution & Allure", "Run generated scripts and view Allure reports."),
        ("artifacts", "📥 Download Artifacts", "Download generated files from the repository / DB."),
    ]),
    ("🔗 Integrate", [
        ("repo", "⚙️ Source Code / Automation Bridge", "Push generated automation code to your Git repo."),
    ]),
]
TOOL_META = {tid: (label, desc) for _, tools in PHASES for tid, label, desc in tools}

if "active_tool" not in st.session_state:
    st.session_state.active_tool = "recorder"
if "demo_view" not in st.session_state:
    st.session_state.demo_view = "iqea"


# ============================================================================
# PLACEHOLDER TOOL BODIES   (swap these for the real logic later)
# ============================================================================
def _placeholder(note):
    st.info(f"🔌 **Wire-in point** — {note}", icon="🔌")

def render_recorder():
    c1, c2 = st.columns(2)
    c1.radio("Record on", ["Web", "Desktop"], horizontal=True)
    c2.text_input("Page / App name")
    b1, b2, b3 = st.columns(3)
    b1.button("🎥 Start Recording", use_container_width=True)
    b2.button("🛑 Stop Recording", use_container_width=True)
    b3.button("💾 Save Workflow", use_container_width=True, type="primary")
    st.divider()
    st.caption("Captured screenshots preview")
    p = st.columns(4)
    for i, col in enumerate(p, 1):
        col.markdown(f"<div style='background:#EEF1F6;border-radius:8px;height:80px;"
                     f"display:flex;align-items:center;justify-content:center;color:#9AA3B0'>step {i}</div>",
                     unsafe_allow_html=True)
    _placeholder("recorder threads + Quick Script Generator from action_new_xpath_subway_TMT.py (checkbox1 block)")

def render_testcases():
    st.radio("Source", ["Recorded actions", "Documents"], horizontal=True)
    st.text_area("Additional requirements", height=90)
    with st.expander("🔗 Test Management Integration (optional)"):
        st.radio("Tool", ["None", "Azure Test Plans", "Jira"], horizontal=True)
    st.button("Generate Functional Test Cases", type="primary")
    _placeholder("test-case generation + gap analysis + Azure DevOps push (checkbox3 block)")

def render_bdd():
    st.text_input("Feature file name")
    st.multiselect("Action files", ["login_actions.txt", "checkout_actions.txt"])
    st.button("Generate Feature File", type="primary")
    _placeholder("BDD generator (checkbox2 block)")

def render_testdata():
    st.text_input("Test data set name")
    st.multiselect("Based on action files", ["login_actions.txt", "checkout_actions.txt"])
    st.text_area("Extra instructions", height=80)
    st.button("Generate Test Data", type="primary")
    _placeholder("test-data generator (checkbox4 block)")

def render_pom():
    st.text_input("Page name")
    st.multiselect("Element tags", ["input", "button", "a", "select"], default=["input", "button"])
    st.button("Generate Locators + POM", type="primary")
    _placeholder("locator/XPath + POM generator (checkbox5 block)")

def render_scripts():
    st.selectbox("Language / framework",
                 ["Python-Selenium", "Python-Playwright", "Java-Selenium", "Java-Playwright"])
    c1, c2 = st.columns(2)
    c1.multiselect("Page files", ["LoginPage.py", "CheckoutPage.py"])
    c2.multiselect("Test cases", ["TC_Login", "TC_Checkout"])
    st.button("Generate Script", type="primary")
    _placeholder("script generator + editor + review feedback (checkbox6 block)")

def render_execute():
    st.multiselect("Scripts to run", ["test_login.py", "test_checkout.py"])
    c1, c2 = st.columns(2)
    c1.button("▶️ Run Tests", type="primary", use_container_width=True)
    c2.button("📊 View Allure Report", use_container_width=True)
    _placeholder("execution + Allure serve (checkbox9 block)")

def render_artifacts():
    st.multiselect("Artifacts", ["Page files", "Test cases", "Scripts", "Feature files"])
    st.button("📥 Download", type="primary")
    _placeholder("artifact download from DB (checkbox8 block)")

def render_repo():
    st.text_input("Repository URL")
    st.selectbox("Provider", ["GitHub", "GitLab"])
    st.button("⬆️ Push to Repository", type="primary")
    _placeholder("repo push (checkbox7 block)")

RENDERERS = {
    "recorder": render_recorder, "testcases": render_testcases, "bdd": render_bdd,
    "testdata": render_testdata, "pom": render_pom, "scripts": render_scripts,
    "execute": render_execute, "artifacts": render_artifacts, "repo": render_repo,
}


# ============================================================================
# IQEA WORKBENCH  (left rail + single workspace)
# ============================================================================
def iqea_workbench():
    st.markdown(
        "<div class='ctx-bar'>"
        "<p class='ctx-title'>🤖 iQEA — Intelligent QE Assistant</p>"
        "<p class='ctx-sub'>Pick any tool on the left — each runs independently, no sequence required.</p>"
        "</div>", unsafe_allow_html=True)

    # shared context bar (browser session lives here, above all tools)
    cb = st.container(border=True)
    with cb:
        u1, u2 = st.columns([5, 1])
        u1.text_input("Target URL", placeholder="https://www.saucedemo.com", label_visibility="collapsed")
        u2.button("Open Browser", use_container_width=True, type="primary")

    rail, work = st.columns([1, 3.4], gap="medium")

    # ---- left tool rail (grouped by phase) ----
    with rail:
        with st.container():
            st.markdown("<div class='rail-card'>", unsafe_allow_html=True)
            for phase_name, tools in PHASES:
                st.markdown(f"<div class='rail-phase'>{phase_name}</div>", unsafe_allow_html=True)
                for tid, label, _desc in tools:
                    active = st.session_state.active_tool == tid
                    if st.button(label, key=f"nav_{tid}", use_container_width=True,
                                 type="primary" if active else "secondary"):
                        st.session_state.active_tool = tid
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ---- right workspace (one tool only) ----
    with work:
        tid = st.session_state.active_tool
        label, desc = TOOL_META[tid]
        st.markdown(f"<div class='ws-card'><p class='ws-head'>{label}</p>"
                    f"<p class='ws-desc'>{desc}</p>", unsafe_allow_html=True)
        RENDERERS[tid]()
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# API VALIDATOR  (redesigned: mode segmented + sub-tabs)
# ============================================================================
def api_validator():
    st.markdown(
        "<div class='ctx-bar'>"
        "<p class='ctx-title'>🔗 API Validator</p>"
        "<p class='ctx-sub'>Validate, benchmark and analyze APIs — one focused panel per concern.</p>"
        "</div>", unsafe_allow_html=True)

    src = st.segmented_control("Source", ["📄 Document (Excel)", "🌐 Swagger / OpenAPI"],
                               default="📄 Document (Excel)")

    with st.container(border=True):
        if src and "Swagger" in src:
            c1, c2 = st.columns([4, 1])
            c1.text_input("Swagger / OpenAPI URL", placeholder="https://.../swagger.json",
                          label_visibility="collapsed")
            c2.button("Fetch APIs", use_container_width=True, type="primary")
        else:
            c1, c2 = st.columns([3, 1])
            c1.file_uploader("Upload API Excel", type=["xlsx"], label_visibility="collapsed")
            c2.download_button("⬇ Template", data=b"demo", file_name="API_Test_Template.xlsx",
                               use_container_width=True)

    tab_v, tab_p, tab_ai = st.tabs(["🧪 Validation", "⚡ Performance", "🤖 AI Insights"])

    with tab_v:
        st.caption("Select endpoints, then run. Results render here — no scrolling past other panels.")
        st.dataframe({"Method": ["GET", "POST"], "Endpoint": ["/users", "/orders"],
                      "Status": [200, 201], "Result": ["PASS", "PASS"]}, use_container_width=True)
        st.button("Run Validation", type="primary")

    with tab_p:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Response", "142 ms")
        c2.metric("p95", "310 ms")
        c3.metric("RPS", "48")
        c4.metric("Failures", "0")
        st.button("Run Performance Test", type="primary")
        _placeholder("Locust performance run + report embed")

    with tab_ai:
        st.caption("LLM recommendations on responses and performance land here.")
        _placeholder("api_response_prompt / locust_convert_prompt HTML reports")


# ============================================================================
# TOP-LEVEL DEMO SWITCH  (prototype only — real app uses the main sidebar)
# ============================================================================
top = st.columns([1, 1, 6])
if top[0].button("🧠 IQEA Workbench", use_container_width=True,
                 type="primary" if st.session_state.demo_view == "iqea" else "secondary"):
    st.session_state.demo_view = "iqea"; st.rerun()
if top[1].button("🔗 API Validator", use_container_width=True,
                 type="primary" if st.session_state.demo_view == "api" else "secondary"):
    st.session_state.demo_view = "api"; st.rerun()

st.write("")
if st.session_state.demo_view == "iqea":
    iqea_workbench()
else:
    api_validator()
