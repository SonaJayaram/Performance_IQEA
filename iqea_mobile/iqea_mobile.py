import streamlit as st
import json
import time
import random
import string
from datetime import datetime

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IQEA | Mobile Automation",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

:root {
    --bg: #0a0c10;
    --surface: #111318;
    --surface2: #181b22;
    --border: #252830;
    --accent: #00e5ff;
    --accent2: #7c3aed;
    --success: #00e676;
    --warn: #ffab00;
    --danger: #ff1744;
    --text: #e8eaf0;
    --muted: #6b7280;
    --mono: 'Space Mono', monospace;
    --sans: 'Syne', sans-serif;
}

html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem !important; max-width: 1400px !important; }

/* ── Top Header Bar ── */
.iqea-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.iqea-logo {
    font-family: var(--sans);
    font-weight: 800;
    font-size: 1.6rem;
    letter-spacing: -0.03em;
    color: var(--accent);
}
.iqea-logo span { color: var(--text); }
.iqea-badge {
    font-family: var(--mono);
    font-size: 0.7rem;
    background: var(--accent2);
    color: #fff;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ── Section Cards ── */
.section-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.4rem;
    position: relative;
    overflow: hidden;
}
.section-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, var(--accent), var(--accent2));
}
.section-title {
    font-family: var(--sans);
    font-weight: 700;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px; height: 22px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #000;
    font-size: 0.7rem;
    font-weight: 700;
}

/* ── Status Pill ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: var(--mono);
    font-size: 0.72rem;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 400;
}
.status-idle    { background: #1a1a2e; color: var(--muted); border: 1px solid var(--border); }
.status-live    { background: #0a2e1a; color: var(--success); border: 1px solid var(--success)33; }
.status-warn    { background: #2e1a00; color: var(--warn);    border: 1px solid var(--warn)33; }
.status-error   { background: #2e000a; color: var(--danger);  border: 1px solid var(--danger)33; }
.dot { width:7px; height:7px; border-radius:50%; }
.dot-green  { background: var(--success); box-shadow: 0 0 6px var(--success); animation: blink 1.2s infinite; }
.dot-grey   { background: var(--muted); }
.dot-yellow { background: var(--warn); box-shadow: 0 0 6px var(--warn); animation: blink 1.2s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

/* ── Action Log Terminal ── */
.terminal {
    background: #060810;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    font-family: var(--mono);
    font-size: 0.72rem;
    max-height: 260px;
    overflow-y: auto;
    color: #a0aec0;
    line-height: 1.7;
}
.terminal .log-line { padding: 1px 0; }
.terminal .log-action { color: var(--accent); }
.terminal .log-xpath  { color: #fbbf24; }
.terminal .log-ts     { color: var(--muted); }
.terminal .log-ok     { color: var(--success); }
.terminal .log-err    { color: var(--danger); }

/* ── Generated Script Box ── */
.code-block {
    background: #060810;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-family: var(--mono);
    font-size: 0.72rem;
    white-space: pre-wrap;
    color: #a0aec0;
    max-height: 420px;
    overflow-y: auto;
    line-height: 1.75;
}

/* ── Streamlit widget overrides ── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}
.stButton > button {
    font-family: var(--sans) !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
    transition: all .2s !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), #0096aa) !important;
    color: #000 !important;
}
.stButton > button[kind="secondary"] {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}
.stTextInput > div > div > input {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
}
.stRadio > div { gap: 8px; }
.stRadio label { font-family: var(--sans) !important; }
.stDownloadButton > button {
    background: var(--surface2) !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: var(--sans) !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}
div[data-testid="column"] { gap: 0 !important; }
.stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ────────────────────────────────────────────────────────
for k, v in {
    "device_connected": False,
    "recording": False,
    "actions": [],
    "actions_saved": False,
    "saved_filename": "",
    "generated_script": "",
    "connection_type": None,
    "selected_device": None,
    "session_id": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Device Database ──────────────────────────────────────────────────────────
DEVICES = {
    "Android": {
        "Samsung Galaxy S24 Ultra": {"os": "Android 14", "real": True,  "emu": True},
        "Samsung Galaxy S23":       {"os": "Android 13", "real": True,  "emu": True},
        "Google Pixel 8 Pro":       {"os": "Android 14", "real": True,  "emu": True},
        "Google Pixel 7":           {"os": "Android 13", "real": True,  "emu": True},
        "OnePlus 12":               {"os": "Android 14", "real": True,  "emu": False},
        "Xiaomi 14 Pro":            {"os": "Android 14", "real": True,  "emu": False},
        "Android Emulator (API 34)":{"os": "Android 14", "real": False, "emu": True},
        "Android Emulator (API 33)":{"os": "Android 13", "real": False, "emu": True},
    },
    "iOS": {
        "iPhone 15 Pro Max": {"os": "iOS 17",   "real": True,  "emu": True},
        "iPhone 15":         {"os": "iOS 17",   "real": True,  "emu": True},
        "iPhone 14 Pro":     {"os": "iOS 16",   "real": True,  "emu": True},
        "iPhone 13":         {"os": "iOS 15",   "real": True,  "emu": True},
        "iPad Pro 12.9":     {"os": "iPadOS 17","real": True,  "emu": True},
        "iPhone 15 Pro Sim": {"os": "iOS 17",   "real": False, "emu": True},
        "iPhone 14 Sim":     {"os": "iOS 16",   "real": False, "emu": True},
    },
}

SCRIPT_TEMPLATES = {
    "Python + Appium (Selenium)": {
        "ext": "py",
        "imports": """import pytest
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
""",
        "driver_android": """
def create_driver():
    desired_caps = {{
        "platformName": "{platform}",
        "deviceName": "{device}",
        "platformVersion": "{os_ver}",
        "app": "/path/to/your/app.apk",   # Update path
        "automationName": "UIAutomator2",
        "noReset": True,
    }}
    driver = webdriver.Remote("http://localhost:4723/wd/hub", desired_caps)
    return driver
""",
        "action_tap": '    driver.find_element(AppiumBy.XPATH, "{xpath}").click()  # {label}',
        "action_input": '    driver.find_element(AppiumBy.XPATH, "{xpath}").send_keys("{value}")  # {label}',
        "action_swipe": '    driver.swipe(start_x={sx}, start_y={sy}, end_x={ex}, end_y={ey}, duration=500)  # {label}',
        "wait": '    WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.XPATH, "{xpath}")))',
    },
    "Python + Playwright Mobile": {
        "ext": "py",
        "imports": """import pytest
from playwright.sync_api import sync_playwright, expect
""",
        "driver_android": """
def run_mobile_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            **p.devices["{device}"]  # Update device name for Playwright
        )
        page = context.new_page()
""",
        "action_tap": '        page.locator(\'xpath={xpath}\').click()  # {label}',
        "action_input": '        page.locator(\'xpath={xpath}\').fill("{value}")  # {label}',
        "action_swipe": '        # Swipe: ({sx},{sy}) → ({ex},{ey}) — {label}',
        "wait": '        page.locator(\'xpath={xpath}\').wait_for()',
    },
    "Java + Appium (TestNG)": {
        "ext": "java",
        "imports": """import io.appium.java_client.AppiumDriver;
import io.appium.java_client.MobileElement;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.annotations.*;
import java.net.URL;
""",
        "driver_android": """
    private AppiumDriver<MobileElement> driver;

    @BeforeClass
    public void setUp() throws Exception {{
        DesiredCapabilities caps = new DesiredCapabilities();
        caps.setCapability("platformName", "{platform}");
        caps.setCapability("deviceName", "{device}");
        caps.setCapability("platformVersion", "{os_ver}");
        caps.setCapability("app", "/path/to/app.apk");
        caps.setCapability("automationName", "UIAutomator2");
        driver = new AndroidDriver<>(new URL("http://localhost:4723/wd/hub"), caps);
    }}
""",
        "action_tap": '        driver.findElement(By.xpath("{xpath}")).click(); // {label}',
        "action_input": '        driver.findElement(By.xpath("{xpath}")).sendKeys("{value}"); // {label}',
        "action_swipe": '        // Swipe ({sx},{sy}) → ({ex},{ey}) — {label}',
        "wait": '        new WebDriverWait(driver, 10).until(ExpectedConditions.presenceOfElementLocated(By.xpath("{xpath}")));',
    },
    "JavaScript + WebdriverIO": {
        "ext": "js",
        "imports": """const { remote } = require('webdriverio');
""",
        "driver_android": """
async function main() {{
    const driver = await remote({{
        path: '/wd/hub',
        port: 4723,
        capabilities: {{
            platformName: '{platform}',
            deviceName: '{device}',
            platformVersion: '{os_ver}',
            app: '/path/to/app.apk',
            automationName: 'UIAutomator2',
        }}
    }});
""",
        "action_tap": "    await $('{xpath}').click(); // {label}",
        "action_input": "    await $('{xpath}').setValue('{value}'); // {label}",
        "action_swipe": "    // Swipe ({sx},{sy}) → ({ex},{ey}) — {label}",
        "wait": "    await $('{xpath}').waitForExist({{ timeout: 10000 }});",
    },
    "Robot Framework + AppiumLibrary": {
        "ext": "robot",
        "imports": """*** Settings ***
Library    AppiumLibrary
""",
        "driver_android": """
*** Variables ***
${{PLATFORM}}       {platform}
${{DEVICE}}         {device}
${{APP}}            /path/to/app.apk

*** Keywords ***
Open Mobile App
    Open Application    http://localhost:4723/wd/hub
    ...    platformName=${{PLATFORM}}
    ...    deviceName=${{DEVICE}}
    ...    app=${{APP}}
    ...    automationName=UIAutomator2
""",
        "action_tap": "    Click Element    xpath={xpath}    # {label}",
        "action_input": "    Input Text    xpath={xpath}    {value}    # {label}",
        "action_swipe": "    # Swipe ({sx},{sy}) → ({ex},{ey})    # {label}",
        "wait": "    Wait Until Element Is Visible    xpath={xpath}",
    },
}

# ─── Helpers ──────────────────────────────────────────────────────────────────
def gen_xpath(element_type: str, label: str) -> str:
    templates = {
        "button":   [f'//android.widget.Button[@content-desc="{label}"]',
                     f'//XCUIElementTypeButton[@name="{label}"]'],
        "input":    [f'//android.widget.EditText[@resource-id="com.app:id/{label.lower().replace(" ","_")}"]',
                     f'//XCUIElementTypeTextField[@name="{label}"]'],
        "text":     [f'//android.widget.TextView[@text="{label}"]',
                     f'//XCUIElementTypeStaticText[@name="{label}"]'],
        "image":    [f'//android.widget.ImageView[@content-desc="{label}"]',
                     f'//XCUIElementTypeImage[@name="{label}"]'],
        "checkbox": [f'//android.widget.CheckBox[@text="{label}"]',
                     f'//XCUIElementTypeSwitch[@name="{label}"]'],
    }
    return random.choice(templates.get(element_type, templates["button"]))

def gen_session_id():
    return "SES-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def format_actions_as_json(actions, device, platform, conn_type):
    return json.dumps({
        "session_id": st.session_state.session_id,
        "device": device,
        "platform": platform,
        "connection": conn_type,
        "recorded_at": datetime.now().isoformat(),
        "actions": actions,
    }, indent=2)

def generate_script(actions, device, platform, os_ver, framework):
    tpl = SCRIPT_TEMPLATES[framework]
    lines = []
    ext = tpl["ext"]

    # Header comment
    lines.append(f"{'#' if ext in ('py','robot') else '//'} ═══════════════════════════════════════")
    lines.append(f"{'#' if ext in ('py','robot') else '//'} IQEA Auto-Generated Mobile Test Script")
    lines.append(f"{'#' if ext in ('py','robot') else '//'} Device   : {device}")
    lines.append(f"{'#' if ext in ('py','robot') else '//'} Platform : {platform} {os_ver}")
    lines.append(f"{'#' if ext in ('py','robot') else '//'} Framework: {framework}")
    lines.append(f"{'#' if ext in ('py','robot') else '//'} Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"{'#' if ext in ('py','robot') else '//'} ═══════════════════════════════════════\n")

    lines.append(tpl["imports"])
    lines.append(tpl["driver_android"].format(platform=platform, device=device, os_ver=os_ver))

    if ext == "robot":
        lines.append("*** Test Cases ***")
        lines.append("Recorded Mobile Test")
    elif ext in ("py",):
        if "pytest" in tpl["imports"]:
            lines.append("def test_recorded_flow():")
            lines.append("    driver = create_driver()")
        else:
            lines.append("        # Recorded Actions")

    for idx, action in enumerate(actions):
        xpath = action.get("xpath", "//android.widget.TextView[@text='unknown']")
        label = action.get("label", f"element_{idx}")
        atype = action.get("type", "tap")
        value = action.get("value", "")
        sx, sy = action.get("start", (100, 500))
        ex, ey = action.get("end", (100, 200))

        if atype == "tap":
            lines.append(tpl["action_tap"].format(xpath=xpath, label=label))
        elif atype == "input":
            lines.append(tpl["action_input"].format(xpath=xpath, label=label, value=value))
        elif atype == "swipe":
            lines.append(tpl["action_swipe"].format(sx=sx, sy=sy, ex=ex, ey=ey, label=label))

    if ext == "py" and "sync_playwright" not in tpl["imports"]:
        lines.append("\n    driver.quit()")
    elif ext == "js":
        lines.append("\n    await driver.deleteSession();\n}\nmain();")

    return "\n".join(lines)

# ─── Simulated Action Recorder ────────────────────────────────────────────────
DEMO_ACTIONS = [
    {"type": "tap",   "label": "Login Button",       "xpath": '//android.widget.Button[@content-desc="Login"]'},
    {"type": "input", "label": "Username Field",     "xpath": '//android.widget.EditText[@resource-id="com.app:id/username"]', "value": "test_user"},
    {"type": "input", "label": "Password Field",     "xpath": '//android.widget.EditText[@resource-id="com.app:id/password"]', "value": "••••••••"},
    {"type": "tap",   "label": "Submit Button",      "xpath": '//android.widget.Button[@content-desc="Submit"]'},
    {"type": "swipe", "label": "Scroll Down",        "xpath": "",  "start": [540, 1600], "end": [540, 400]},
    {"type": "tap",   "label": "Profile Menu",       "xpath": '//android.widget.ImageView[@content-desc="Profile"]'},
    {"type": "tap",   "label": "Settings Option",    "xpath": '//android.widget.TextView[@text="Settings"]'},
    {"type": "tap",   "label": "Notifications Toggle","xpath": '//android.widget.Switch[@text="Notifications"]'},
]

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="iqea-header">
  <div style="display:flex;align-items:center;gap:14px">
    <div class="iqea-logo">IQ<span>EA</span></div>
    <div class="iqea-badge">Mobile Automation</div>
  </div>
  <div style="font-family:var(--mono);font-size:.72rem;color:var(--muted)">
    Intelligent QA & Engineering Automation
  </div>
</div>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Device Selection
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-card">
  <div class="section-title">
    <span class="step-num">1</span> Device Selection
  </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    platform = st.selectbox("Platform", ["Android", "iOS"], key="platform_sel")

with col2:
    device_list = list(DEVICES[platform].keys())
    selected_device = st.selectbox("Device Model", device_list, key="device_sel")
    device_info = DEVICES[platform][selected_device]

with col3:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-top:6px">
      <div style="font-size:.68rem;color:var(--muted);font-family:var(--mono)">OS VERSION</div>
      <div style="font-weight:700;color:var(--accent);font-family:var(--mono)">{device_info['os']}</div>
    </div>
    """, unsafe_allow_html=True)

# Connection type
st.markdown("<div style='margin-top:.5rem'></div>", unsafe_allow_html=True)
col_a, col_b = st.columns(2)

with col_a:
    conn_options = []
    if device_info["real"]:  conn_options.append("🔌  Real Device (USB)")
    if device_info["emu"]:   conn_options.append("☁️  Emulator / BrowserStack")
    connection_type = st.radio("Connection Mode", conn_options, horizontal=True, key="conn_type")

with col_b:
    app_type = st.radio("App Type", ["📱  Native App", "🌐  Mobile Browser"], horizontal=True, key="app_type")

# App details
if "Native" in app_type:
    col_x, col_y = st.columns([2, 1])
    with col_x:
        app_path = st.text_input("App Path / Package", placeholder="e.g. com.example.app  or  /path/to/app.apk", key="app_path")
    with col_y:
        browser_name = st.selectbox("Auto. Engine", ["UIAutomator2", "XCUITest", "Espresso"], key="engine")
else:
    col_x, col_y = st.columns([1, 1])
    with col_x:
        browser_name = st.selectbox("Browser", ["Chrome", "Safari", "Firefox"], key="browser_sel")
    with col_y:
        start_url = st.text_input("Start URL", placeholder="https://example.com", key="start_url")

# ─ Connect Button ─
st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
if not st.session_state.device_connected:
    if st.button("⚡  Connect Device", type="primary", key="connect_btn"):
        with st.spinner("Establishing connection..."):
            time.sleep(1.5)
        st.session_state.device_connected = True
        st.session_state.selected_device = selected_device
        st.session_state.connection_type = connection_type
        st.session_state.session_id = gen_session_id()
        st.success(f"✅ Connected to **{selected_device}** via {'USB' if 'Real' in connection_type else 'BrowserStack'}")
        st.rerun()
else:
    cstatus = "Real Device (USB)" if "Real" in st.session_state.connection_type else "BrowserStack Emulator"
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;padding:.5rem 0">
      <span class="status-pill status-live"><span class="dot dot-green"></span>Connected</span>
      <span style="font-family:var(--mono);font-size:.72rem;color:var(--muted)">{st.session_state.selected_device} · {cstatus} · {st.session_state.session_id}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔌  Disconnect", type="secondary", key="disconnect_btn"):
        for k in ["device_connected", "recording", "actions", "actions_saved", "generated_script", "session_id"]:
            st.session_state[k] = False if k in ("device_connected","recording","actions_saved") else [] if k == "actions" else ""
        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Action Recording
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-card" style="margin-top:1.6rem">
  <div class="section-title">
    <span class="step-num">2</span> Action Recording
  </div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.device_connected:
    st.markdown("""
    <div class="status-pill status-idle" style="margin-bottom:.5rem">
      <span class="dot dot-grey"></span> Waiting for device connection…
    </div>
    """, unsafe_allow_html=True)
else:
    col_rec1, col_rec2, col_rec3 = st.columns([1, 1, 2])

    with col_rec1:
        if not st.session_state.recording:
            if st.button("⏺  Start Recording", type="primary", key="rec_start"):
                st.session_state.recording = True
                st.session_state.actions = []
                st.rerun()
        else:
            if st.button("⏹  Stop Recording", type="secondary", key="rec_stop"):
                st.session_state.recording = False
                st.rerun()

    with col_rec2:
        if st.session_state.recording:
            # Simulate capturing an action
            if st.button("➕  Capture Action (Demo)", key="cap_action"):
                idx = len(st.session_state.actions) % len(DEMO_ACTIONS)
                st.session_state.actions.append({
                    **DEMO_ACTIONS[idx],
                    "ts": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    "seq": len(st.session_state.actions) + 1,
                })
                st.rerun()

    with col_rec3:
        if st.session_state.recording:
            st.markdown("""
            <span class="status-pill status-live">
              <span class="dot dot-green"></span> Recording in progress…
            </span>
            """, unsafe_allow_html=True)
        elif st.session_state.actions:
            st.markdown(f"""
            <span class="status-pill status-warn">
              <span class="dot dot-yellow"></span> {len(st.session_state.actions)} actions recorded
            </span>
            """, unsafe_allow_html=True)

    # ─ Action Log Terminal ─
    if st.session_state.actions:
        log_html = '<div class="terminal">'
        for a in st.session_state.actions:
            seq = a["seq"]
            ts  = a["ts"]
            typ = a["type"].upper()
            lbl = a["label"]
            xp  = a.get("xpath", "")
            log_html += f'<div class="log-line"><span class="log-ts">[{ts}]</span> <span class="log-action">#{seq:02d} {typ}</span> — {lbl}'
            if xp:
                log_html += f'<br>&nbsp;&nbsp;&nbsp;&nbsp;<span class="log-xpath">{xp}</span>'
            log_html += '</div>'
        log_html += "</div>"
        st.markdown(log_html, unsafe_allow_html=True)
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # ─ Save Actions ─
        col_s1, col_s2 = st.columns([1, 3])
        with col_s1:
            fname = st.text_input("Filename", value=f"recorded_{datetime.now().strftime('%Y%m%d_%H%M%S')}", key="fname")
        with col_s2:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            actions_json = format_actions_as_json(
                st.session_state.actions,
                st.session_state.selected_device,
                platform,
                st.session_state.connection_type or ""
            )
            st.download_button(
                label="💾  Download Actions JSON",
                data=actions_json,
                file_name=f"{fname}.json",
                mime="application/json",
                key="dl_actions"
            )
            st.session_state.actions_saved = True
            st.session_state.saved_filename = fname

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Script Generation
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-card" style="margin-top:1.6rem">
  <div class="section-title">
    <span class="step-num">3</span> Script Generation
  </div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.actions:
    st.markdown("""
    <div class="status-pill status-idle">
      <span class="dot dot-grey"></span> Record and save actions first to generate a script
    </div>
    """, unsafe_allow_html=True)
else:
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        framework = st.selectbox(
            "Language + Framework",
            list(SCRIPT_TEMPLATES.keys()),
            key="framework_sel"
        )
    with col_f2:
        add_waits = st.checkbox("Add explicit waits", value=True, key="add_waits")
        add_comments = st.checkbox("Add inline comments", value=True, key="add_comments")

    if st.button("⚙️  Generate Script", type="primary", key="gen_script"):
        with st.spinner("Generating test script…"):
            time.sleep(0.8)
        dev_info = DEVICES[platform].get(st.session_state.selected_device, {"os": "Unknown"})
        st.session_state.generated_script = generate_script(
            st.session_state.actions,
            st.session_state.selected_device,
            platform,
            dev_info["os"],
            framework
        )
        st.rerun()

    if st.session_state.generated_script:
        tpl_ext = SCRIPT_TEMPLATES[framework]["ext"]
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;margin:.8rem 0 .4rem">
          <span style="font-family:var(--mono);font-size:.72rem;color:var(--muted)">
            Generated · {framework} · {len(st.session_state.generated_script.splitlines())} lines
          </span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f'<div class="code-block">{st.session_state.generated_script}</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

        col_dl1, col_dl2 = st.columns([1, 4])
        with col_dl1:
            st.download_button(
                label=f"⬇️  Download .{tpl_ext}",
                data=st.session_state.generated_script,
                file_name=f"iqea_mobile_test.{tpl_ext}",
                mime="text/plain",
                key="dl_script"
            )

# ─ Footer ─
st.markdown("""
<div style="text-align:center;margin-top:3rem;padding-top:1rem;border-top:1px solid var(--border);
     font-family:var(--mono);font-size:.65rem;color:var(--muted)">
  IQEA Platform · Mobile Automation Module · Built with Streamlit + Appium
</div>
""", unsafe_allow_html=True)