import os
import streamlit as st
import streamlit.components.v1 as components  # ✅ Fixed: Namespace declared correctly to support live panel streaming

# ==============================================================================
# 🔐 SECURE ENVIRONMENT INJECTION FROM SECRETS
# ==============================================================================
# This automatically maps parameters from your secrets.toml straight to the Azure
# SDK environment variables before any sub-modules or backend tools load up.
for key in ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"]:
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

# ==============================================================================
# STANDARD LIBRARY & THIRD PARTY IMPORTS
# ==============================================================================
import threading
import tempfile
import sys
import subprocess
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from streamlit.runtime.scriptrunner import add_script_run_ctx  # Clears Multi-threading Context Warnings

# Add proper directory scopes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities import utils_action as action_utils
import utilities.Utilities_Xpath as utils
import desktop
import utilitymodule
from desktop.recorder import DesktopRecorder
from desktop.session import DesktopSession
from config.settings_reader import get_source, get_update_user, get_model, get_xpath_key

# Directory paths setup
current_path = os.getcwd()
page_screenshot_folder = os.path.join(current_path, "demofolder")
Action_collection = os.path.join(current_path, "actions_workspaces")
Action_collection_desktop = os.path.join(Action_collection, "Action_collection_desktop")
source = get_source()

# ---------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------
st.set_page_config(
    page_title="TigerQE AI iQEA",
    page_icon="🤖",
    layout="wide"  # Side-by-side split execution alignment view
)

# ---------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------
default_states = {
    "checkbox1_state": True,
    "checkbox2_state": False,
    "checkbox3_state": True,
    "checkbox4_state": True,
    "checkbox5_state": True,
    "checkbox6_state": True,
    "checkbox7_state": True,
    "checkbox8_state": True,
    "checkbox9_state": True,
    "recording_started": False,
    "driver": None,
    "actions": [],
    "workflow_text": [],
    "injected_windows": {},
    "last_urls": {},
    "current_window_ref": {"handle": None},
    "stop_monitor": {"stop": False},
    "monitor_threads": [],
    "generated_jmx": "",
    "generated_jmx_path": ""
}

for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------------------------------
# TITLE HEADER
# ---------------------------------------------------
st.title("🤖 TigerQE AI Platform - Performance Testing")
st.markdown("---")

# ==============================================================================
# 📊 ✨ GRAFANA CONFIGURATION MANAGEMENT SIDEBAR PANEL
# ==============================================================================
st.sidebar.header("📊 Grafana Local Core Controls")
st.sidebar.markdown("Paste your copied isolated panel **Embed links** below:")
live_rt_panel = st.sidebar.text_input(
    "Live Test Latency Panel Link",
    value="",
    placeholder="e.g., http://localhost:3000/d-solo/jm_metrics/jmeter?refresh=5s&panelId=2"
)
live_server_panel = st.sidebar.text_input(
    "Live Host Server Metric Panel Link",
    value="",
    placeholder="e.g., http://localhost:3000/d-solo/tel_metrics/server?refresh=5s&panelId=5"
)
# ---------------------------------------------------
# TWO-SECTION UI LAYOUT SPLIT
# ---------------------------------------------------
col_prompt, col_recorder = st.columns(2, gap="large")

# ===================================================
# SECTION 1: ORIGINAL PROMPT FLOW (LEFT COLUMN)
# ===================================================
with col_prompt:
    st.header("📋 Original Prompt Flow")

    # Folder to save generated JMX files
    JMX_FOLDER = "generated_jmx_files"
    os.makedirs(JMX_FOLDER, exist_ok=True)

    if st.session_state.checkbox5_state:
        with st.expander("🔎 JMX script generator", expanded=True):
            st.subheader("JMX using prompt")
            st.markdown("Enter your prompt for generating a JMeter (.jmx) script.")

            script_name = st.text_input(
                "Enter JMX File Name",
                value="generated_test_plan",
                key="prompt_script_name"
            )

            user_prompt = st.text_area(
                "Enter Prompt",
                height=250,
                max_chars=5000,
                placeholder="""Example:\n\nGenerate a JMeter JMX script for:\n1. Login API\n2. Search product API...""",
                key="prompt_user_input"
            )

            if st.button("Generate JMX Script", key="btn_generate_jmx"):
                if not user_prompt.strip():
                    st.error("Please enter a prompt.")
                else:
                    with st.spinner("Generating JMX Script..."):
                        try:
                            response = utilitymodule.get_output_from_ai(user_prompt)
                            if response is None:
                                st.error("❌ AI did not return any response.")
                            else:
                                response = str(response)
                                st.session_state.generated_jmx = response

                                file_name = f"{script_name}.jmx"
                                file_path = os.path.join(JMX_FOLDER, file_name)

                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(response)

                                st.session_state.generated_jmx_path = file_path
                                st.success("✅ JMX generated and saved successfully.")
                                st.info(f"Saved Location: {file_path}")
                        except Exception as e:
                            st.error(f"❌ Error generating JMX: {e}")

            if st.session_state.generated_jmx:
                st.subheader("Generated JMX Output")
                st.text_area("JMX Output Raw", value=st.session_state.generated_jmx, height=250)

                st.download_button(
                    label="⬇ Download JMX File",
                    data=st.session_state.generated_jmx,
                    file_name=f"{script_name}.jmx",
                    mime="application/xml",
                    key="dl_prompt_jmx"
                )

            st.subheader("Saved JMX Scripts Repository")
            saved_files = [f for f in os.listdir(JMX_FOLDER) if f.endswith(".jmx")]

            if saved_files:
                selected_saved_file = st.selectbox("Select Saved JMX File", saved_files, key="sb_saved_files_prompt")
                selected_file_path = os.path.join(JMX_FOLDER, selected_saved_file)
                st.success(f"Selected File: {selected_saved_file}")
                st.session_state.generated_jmx_path = selected_file_path
            else:
                st.info("No saved JMX scripts found.")

# ===================================================
# SECTION 2: REAL USER ACTION RECORDING (RIGHT COLUMN)
# ===================================================
with col_recorder:
    st.header("🎥 Real User Action Recording")

    st.subheader("🔗 Target Environment Initialization")
    page_url = st.text_input("Enter the URL of the page:", key="recorder_url_input")

    if st.button("Open Browser", key="btn_open_browser"):
        if not page_url.strip():
            st.error("Please enter a valid URL.")
        else:
            try:
                chrome_options = Options()
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--remote-allow-origins=*")

                driver = webdriver.Chrome(options=chrome_options)
                st.session_state.driver = driver
                st.session_state.driver.get(page_url)

                WebDriverWait(st.session_state.driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                st.success(f"✅ Browser opened successfully: {page_url}")
            except Exception as e:
                st.error(f"❌ Failed to open browser: {e}")

    if st.session_state.checkbox1_state:
        with st.expander("🔴 User Workflow Recorder", expanded=True):
            option = st.radio("Choose where to record:", ("Web", "Desktop"), key="radio_record_target")

            if option == "Web":
                st.caption("Record User Actions & Capture Screenshots of User Navigation")

                if not st.session_state.recording_started and st.button("🎥 Start Recording", key="btn_start_rec"):
                    try:
                        driver = st.session_state.driver
                        if not driver:
                            st.error("Driver not initialized. Please click 'Open Browser' first.")
                        else:
                            st.session_state.actions.clear()
                            st.session_state.workflow_text.clear()
                            st.session_state.stop_monitor["stop"] = True

                            for t in st.session_state.monitor_threads:
                                if t and t.is_alive():
                                    t.join(timeout=2)

                            st.session_state.stop_monitor = {"stop": False}
                            st.session_state.monitor_threads = []
                            st.session_state.injected_windows = {}
                            st.session_state.last_urls = {}
                            st.session_state.current_window_ref = {"handle": driver.current_window_handle}

                            driver.execute_script(action_utils.injection_script_updated_fixed())
                            current_handle = driver.current_window_handle
                            st.session_state.injected_windows[current_handle] = True

                            # Background threads creation
                            t1 = threading.Thread(target=utils.thread_new_window_checker,
                                                  args=(driver, st.session_state.injected_windows,
                                                        st.session_state.last_urls, st.session_state.stop_monitor,
                                                        page_screenshot_folder, st.session_state.current_window_ref),
                                                  daemon=True)
                            t2 = threading.Thread(target=utils.thread_focus_and_url_monitor,
                                                  args=(driver, st.session_state.injected_windows,
                                                        st.session_state.last_urls, st.session_state.stop_monitor,
                                                        page_screenshot_folder, st.session_state.current_window_ref),
                                                  daemon=True)
                            t3 = threading.Thread(target=utils.thread_focus_screenshot,
                                                  args=(driver, st.session_state.stop_monitor, page_screenshot_folder,
                                                        source), daemon=True)
                            t4 = threading.Thread(target=utils.thread_reinject_action_check,
                                                  args=(driver, st.session_state.stop_monitor,
                                                        st.session_state.last_urls, st.session_state.current_window_ref,
                                                        st.session_state.injected_windows), daemon=True)

                            # --- BIND BACKGROUND THREADS TO THE STREAMLIT RUNTIME CONTEXT ---
                            # This clears out the "missing ScriptRunContext!" dashboard warning exceptions
                            add_script_run_ctx(t1)
                            add_script_run_ctx(t2)
                            add_script_run_ctx(t3)
                            add_script_run_ctx(t4)

                            t1.start()
                            t2.start()
                            t3.start()
                            t4.start()

                            st.session_state.monitor_threads = [t1, t2, t3, t4]
                            st.session_state.recording_started = True
                            st.success("✅ Recording started. Interact with the browser.")
                    except Exception as e:
                        st.error(f"Start recording failed: {e}")

                if st.session_state.recording_started and st.button("🛑 Stop Recording", key="btn_stop_rec"):
                    try:
                        driver = st.session_state.driver
                        recorded_actions = action_utils.get_recorded_actions(driver)
                        if recorded_actions:
                            for act in recorded_actions:
                                if act not in st.session_state.actions:
                                    st.session_state.actions.append(act)

                        st.session_state.stop_monitor["stop"] = True
                        for t in st.session_state.monitor_threads:
                            if t and t.is_alive():
                                t.join(timeout=2)
                        st.session_state.monitor_threads = []
                        st.session_state.recording_started = False
                        st.success(f"✅ Recording stopped. {len(st.session_state.actions)} actions captured.")
                    except Exception as e:
                        st.error(f"Stop recording failed: {e}")

                if st.session_state.actions:
                    st.subheader("Captured Actions")
                    for idx, action in enumerate(st.session_state.actions, start=1):
                        st.write(f"{idx}. {action}")

                    page_name = st.text_input("Enter workflow name:", key="txt_workflow_name")

                    if st.button("💾 Save Workflow", key="btn_save_workflow"):
                        try:
                            if not page_name.strip():
                                st.warning("⚠ Please enter workflow name.")
                                st.stop()

                            workflow_text = action_utils.generate_workflow_manual(st.session_state.actions)


                            def clean_text(s):
                                return s.replace("\u200b", "").replace("\xa0", " ").strip()


                            cleaned = [clean_text(x) for x in workflow_text]

                            filename = os.path.join(Action_collection, f"{page_name}_actions.txt")
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write("\n".join(cleaned))

                            st.success(f"✅ Workflow saved successfully:\n{filename}")
                            st.download_button("⬇ Download Workflow", data="\n".join(cleaned),
                                               file_name=f"{page_name}_actions.txt", mime="text/plain",
                                               key="dl_workflow_txt")

                            clear_actions = """(function() { window.__recordedActions = []; localStorage.removeItem("recordedActions"); console.log("🧹 Cleared recorded actions"); })();"""
                            st.session_state.driver.execute_script(clear_actions)
                        except Exception as e:
                            st.error(f"Save failed: {e}")

    if st.session_state.checkbox3_state:
        with st.expander("🧮 Performance Test Script Generator", expanded=True):
            action_folder = Action_collection
            if not os.path.exists(action_folder):
                st.error("❌ Actions folder not found.")
            else:
                action_files = [f for f in os.listdir(action_folder) if f.endswith("_actions.txt")]
                if not action_files:
                    st.warning("⚠ No recorded workflow files found.")
                else:
                    selected_action_file = st.selectbox("Select Recorded Workflow", options=action_files,
                                                        key="sb_rec_workflow")
                    selected_file_path = os.path.join(action_folder, selected_action_file)

                    try:
                        with open(selected_file_path, "r", encoding="utf-8") as f:
                            actions = [line.strip() for line in f.readlines() if line.strip()]
                    except Exception as e:
                        st.error(f"❌ Failed to read action file:\n{e}")
                        st.stop()

                    st.subheader("📋 Recorded Browser Actions")
                    for idx, action in enumerate(actions, start=1):
                        st.write(f"{idx}. {action}")

                    st.subheader("🤖 AI-based JMX Generation")
                    ai_prompt = st.text_area(
                        "Enter Additional Performance Test Requirements",
                        placeholder="- Generate JMeter JMX\n- Add 100 users\n- Ramp-up time 30 seconds...",
                        height=150,
                        key="ta_perf_requirements"
                    )

                    if st.button("🚀 Generate AI-based JMX", key="btn_gen_ai_jmx"):
                        try:
                            workflow_name = selected_action_file.replace("_actions.txt", "")
                            formatted_actions = "\n".join(
                                [f"{idx + 1}. {action}" for idx, action in enumerate(actions)])

                            # user_prompt = f"""You are an expert JMeter Performance Test Engineer.\n\nConvert the following recorded browser workflow actions into a valid Apache JMeter .jmx test plan.\n\nRequirements:\n1. Generate valid JMX XML only.\n2. Include Test Plan, Thread Group, HTTP Samplers, Managers.\n3. Maintain exact flow.\n4. Do not provide explanation.\n5. Return only XML.\n\nRecorded Browser Actions:\n{formatted_actions}\n\nAdditional Performance Requirements:\n{ai_prompt}"""
                            user_prompt = f""" You are an expert Apache JMeter 5.5 Performance Engineer.
                                                    Convert the recorded browser workflow into a complete, executable Apache JMeter 5.5 JMX test plan.
                                                    
                                                    IMPORTANT OUTPUT RULES:
                                                    1. Return ONLY valid JMeter 5.5 XML (.jmx).
                                                    2. Do not wrap the code in markdown code blocks like ```xml ... ```.
                                                    3. Do not include any explanations, introduction, or conversational filler.
                                                    4. End your response immediately after the closing </jmeterTestPlan> tag.
                                                    5. Generate executable JMX XML only.
                                                    
                                                    JMX STRUCTURE REQUIREMENTS:
                                                    Generate all of the following:
                                                    * Test Plan
                                                    * Thread Group
                                                    * HTTP Request Defaults (Configure domain/protocol here if shared across requests)
                                                    * HTTP Cookie Manager
                                                    * HTTP Cache Manager
                                                    * HTTP Header Manager (Configure Content-Type: application/json globally as required)
                                                    * HTTP Samplers for every recorded action
                                                    * ResultCollector listener (View Results Tree / Summary Report)
                                                    
                                                    THREAD GROUP MAPPING RULES:
                                                    Performance Configuration:
                                                    {ai_prompt}
                                                    
                                                    Apply these mappings exactly:
                                                    threads -> ThreadGroup.num_threads
                                                    rampup -> ThreadGroup.ramp_time
                                                    duration -> ThreadGroup.duration
                                                    
                                                    If duration > 0:
                                                    ThreadGroup.scheduler = true
                                                    
                                                    If loops = -1:
                                                    LoopController.continue_forever = true
                                                    LoopController.loops = -1
                                                    
                                                    If loops > 0:
                                                    LoopController.continue_forever = false
                                                    LoopController.loops = loops
                                                    
                                                    WORKFLOW REQUIREMENTS:
                                                    * Preserve the exact execution order of browser actions.
                                                    * Maintain authentication state using HTTP Cookie Manager.
                                                    * Follow redirects where appropriate and use KeepAlive=true.
                                                    * Ensure explicit connect_timeout and response_timeout tags are generated inside EVERY sampler or inside HTTP Request Defaults, defaulted to "5000".
                                                    * Ensure ThreadGroup.on_sample_error is set exactly to "stopthread" (no spaces) to safely prevent test overruns.
                                                    
                                                    Recorded Browser Actions:
                                                    {formatted_actions}
                                                """
                            with st.spinner("🤖 AI is generating JMX..."):
                                raw_ai_response = utilitymodule.get_output_from_ai(user_prompt)

                            if not raw_ai_response:
                                st.error("❌ Empty response received from AI.")
                                st.stop()

                            # ==============================================================================
                            # 🛡️ SYSTEM FIX: PROGRAMMATIC INFLUX LISTENER INJECTION VIA PYTHON UTILS
                            # ==============================================================================
                            with st.spinner(
                                    "🔧 Calibrating Thread Groups and injecting Backend listeners programmatically..."):
                                # Parse execution user requirements (threads, rampup, duration) out of the input instructions
                                ai_config = utilitymodule.extract_ai_test_config(ai_prompt, raw_ai_response)

                                # Re-run XML tree structuring securely via python to generate the listener nodes cleanly
                                generated_jmx = utilitymodule.update_jmx_file(raw_ai_response.strip(), ai_config)

                            st.subheader("📄 Generated JMX Output")
                            st.code(generated_jmx, language="xml")

                            jmx_output_folder = os.path.join(os.getcwd(), "generated_jmx_files")
                            os.makedirs(jmx_output_folder, exist_ok=True)
                            jmx_filename = os.path.join(jmx_output_folder, f"{workflow_name}.jmx")

                            with open(jmx_filename, "w", encoding="utf-8") as f:
                                f.write(generated_jmx)

                            st.session_state.generated_jmx_path = jmx_filename
                            st.success(f"✅ JMX generated successfully:\n{jmx_filename}")
                            st.download_button(label="⬇ Download JMX File", data=generated_jmx,
                                               file_name=f"{workflow_name}.jmx", mime="application/xml",
                                               key="dl_ai_perf_jmx")
                        except Exception as e:
                            st.error(f"❌ Failed to generate JMX:\n{e}")

# ===================================================
# SECTION 3: TEST EXECUTION & REPORTING (COMMON FOOTER)
# ===================================================
st.markdown("---")
if st.session_state.checkbox9_state:
    with st.expander("🚀 Active Test Execution & Realtime Telemetry Monitoring Console", expanded=True):
        st.title("Execute Generated Test Scripts and View Html Reports")

        jmeter_path = st.text_input(
            "JMeter Executable Path/Command",
            value="jmeter",
            help="Change to complete path if 'jmeter' is not in environment PATH",
            key="execution_jmeter_path"
        )

        saved_jmx_files = []
        if os.path.exists("generated_jmx_files"):
            saved_jmx_files = [f for f in os.listdir("generated_jmx_files") if f.endswith(".jmx")]

        if not saved_jmx_files:
            saved_jmx_files = ["Sample1.jmx", "Sample2.jmx"]

        default_index = 0
        if st.session_state.get("generated_jmx_path"):
            filename_only = os.path.basename(st.session_state.generated_jmx_path)
            if filename_only in saved_jmx_files:
                default_index = saved_jmx_files.index(filename_only)

        selected_file = st.selectbox(
            "Select Test Script to Execute",
            saved_jmx_files,
            index=default_index,
            key="sb_execution_target"
        )

        if selected_file:
            ai_execution_prompt = st.text_area(
                "🤖 AI JMeter Execution Instructions",
                height=150,
                placeholder="Examples:\n- Run smoke test with 2 users\n- Ramp from 1 to 100 users over 5 minutes",
                key="ta_execution_instructions"
            )

            if st.button("Run Test Script", key="btn_run_jmeter_test"):
                user_instruction = ai_execution_prompt.strip()

                if not user_instruction:
                    st.warning(
                        "⚠️ Please provide execution instructions (e.g., 'Run with 5 users') before running the test.")
                else:
                    jmx_full_path = os.path.join("generated_jmx_files", selected_file)

                    if not os.path.exists(jmx_full_path):
                        st.error(f"❌ Selected file layout error: {selected_file} not found locally.")
                    else:
                        with open(jmx_full_path, "r", encoding="utf-8") as f:
                            original_jmx = f.read()

                        base_name = os.path.splitext(selected_file)[0]
                        with st.spinner("🤖 AI analyzing execution instructions..."):
                            ai_config = utilitymodule.extract_ai_test_config(ai_execution_prompt, original_jmx)

                        st.subheader("📋 AI Generated Execution Config")
                        st.json(ai_config)

                        # Parse your new parameters directly into the target JMX layout structure
                        updated_jmx = utilitymodule.update_jmx_file(original_jmx, ai_config)
                        valid, error = utilitymodule.validate_jmx(updated_jmx)

                        if not valid:
                            st.error(f"❌ Invalid JMX generated: {error}")
                            st.stop()

                        st.success("✅ Updated JMX validated successfully")

                        temp_dir = tempfile.gettempdir()
                        updated_test_path = os.path.join(temp_dir, f"updated_{selected_file}")

                        with open(updated_test_path, "w", encoding="utf-8") as f:
                            f.write(updated_jmx)

                        st.success("✅ Temporary updated JMX created")

                        report_base_dir = os.path.join(current_path, "jmeter_reports", base_name)
                        output_jtl = os.path.join(report_base_dir, f"{base_name}_log.jtl")
                        html_report_dir = os.path.join(report_base_dir, "html_dashboard")

                        command = [
                            jmeter_path, "-n",
                            "-t", updated_test_path,
                            "-l", output_jtl,
                            "-e", "-o", html_report_dir,
                            "-Jsummariser.name=summary"
                        ]
                        # ======================================================
                        # 📈 ✨ CHANGED: DYNAMIC REALTIME GRAFANA VIEW PANEL IFRAME STREAM
                        # ======================================================
                        st.markdown("---")
                        st.subheader("📊 Live Telemetry Streaming Dashboard")
                        g_col1, g_col2 = st.columns(2)

                        with g_col1:
                            st.markdown("##### Real-time Test Execution Latency (JMeter)")
                            if live_rt_panel:
                                components.iframe(live_rt_panel, height=380, scrolling=False)
                            else:
                                st.info(
                                    "💡 Input a valid Grafana Response Panel link in the sidebar to visualize execution time arrays.")

                        with g_col2:
                            st.markdown("##### Target Server Resource Profile utilization (Telegraf)")
                            if live_server_panel:
                                components.iframe(live_server_panel, height=380, scrolling=False)
                            else:
                                st.info(
                                    "💡 Input a valid Grafana Server counter panel link in the sidebar to observe CPU/Memory load bounds.")
                        # ======================================================
                        # 📺 LIVE CONSOLE STREAMING OUTPUT TARGET RENDER
                        # ======================================================
                        st.subheader("📺 Live JMeter Console Stream")
                        log_stdout_box = st.empty()  # Interactive placeholder for line additions
                        accumulated_logs = ""

                        with st.spinner("Executing JMeter Script Engine and compiling outputs..."):
                            try:
                                # Ensure execution path trees exist with clean folder profiles
                                os.makedirs(report_base_dir, exist_ok=True)

                                # ==============================================================================
                                # 🛡️ FIXED: SAFE INTERCEPT PROTOCOLS FOR RELEASING WINDOWS FILE LOCKS (WinError 32)
                                # ==============================================================================
                                if os.path.exists(output_jtl):
                                    try:
                                        os.remove(output_jtl)
                                    except OSError:
                                        import time

                                        st.warning(
                                            "⚠️ The existing log file is currently locked by another process. Utilizing a unique runtime log path...")
                                        # Dynamic fallback: Append an epoch timestamp to bypass the lock rule collision completely
                                        output_jtl = os.path.join(report_base_dir,
                                                                  f"{base_name}_log_{int(time.time())}.jtl")

                                if os.path.exists(html_report_dir):
                                    try:
                                        shutil.rmtree(html_report_dir)
                                    except OSError:
                                        # Catch asset locking quietly so execution properties do not halt completely
                                        pass

                                # ==============================================================================
                                # 🚀 ALL ORIGINAL LIVE LOG STREAMING LOGIC REMAINS COMPLETELY UNTOUCHED BELOW
                                # ==============================================================================
                                # Popen standard streaming process call
                                process = subprocess.Popen(
                                    command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True,
                                    bufsize=1,
                                    shell=True
                                )

                                # Continual line validation evaluation loop
                                while True:
                                    line = process.stdout.readline()
                                    if not line and process.poll() is not None:
                                        break
                                    if line:
                                        accumulated_logs += line
                                        log_stdout_box.code(accumulated_logs[-4000:])  # Displays trailing logs slice

                                return_code = process.poll()

                                if return_code == 0:
                                    st.success("✅ JMeter engine completed execution cycle successfully!")
                                    st.info(f"📁 Logs Destination (.jtl): {output_jtl}")
                                    st.info(f"📊 HTML Dashboard Directory: {html_report_dir}")

                                    # ======================================================
                                    # 🖥️ AUTOMATED SERVER METRICS DASHBOARD
                                    # ======================================================
                                    st.markdown("---")
                                    st.subheader("🖥️ Azure Live Host Server Metrics")

                                    with st.spinner("Pulling resource utilization metrics from Azure Monitor..."):
                                        # Calculate runtime length based on your user instruction or fallback default
                                        test_duration_m = max(1, int(ai_config.get("duration", 180)) // 60)

                                        server_data = utilitymodule.get_azure_server_metrics(
                                            duration_minutes=test_duration_m + 1)

                                        if server_data:
                                            m_col1, m_col2 = st.columns(2)
                                            m_col1.metric(
                                                label="Host CPU Utilization",
                                                value=f"{server_data['cpu_time']:.2f}%",  # Changed unit string to %
                                                help="The peak CPU percentage consumed by the Linux web app plan container during the run"
                                            )
                                            m_col2.metric(
                                                label="Host Memory Utilization",
                                                value=f"{server_data['memory_mb']:.2f}%",  # Changed unit string to %
                                                help="Maximum memory footprint percentage allocated during test execution traffic"
                                            )
                                        else:
                                            st.warning(
                                                "⚠️ Cloud metrics lookup failed. Ensure 'QE-Demo-RD' has 'Monitoring Reader' permissions on the App Service.")
                                else:
                                    st.error(f"❌ JMeter process exited with non-zero code: {return_code}")
                                    st.info("Check the streaming logs above to view the exact exception details.")

                            except Exception as ex:
                                st.error(f"❌ Failed to coordinate script execution thread: {ex}")

        if st.button("View Allure Report", key="btn_view_allure"):
            st.success("Allure report functionality will be added here.")

# ---------------------------------------------------
# FOOTER MATRIX SYSTEM DISPLAY CONTROLS
# ---------------------------------------------------
st.divider()
st.markdown("### Contact Us\n- Reach us at [QE Core Team](mailto:sahil.gupta@tigeranalytics.com)")

col0, col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(10)
with col0: st.write("Choose display")
with col1: st.checkbox("(1)", key="checkbox1_state")
with col2: st.checkbox("(2)", key="checkbox2_state")
with col3: st.checkbox("(3)", key="checkbox3_state")
with col4: st.checkbox("(4)", key="checkbox4_state")
with col5: st.checkbox("(5)", key="checkbox5_state")
with col6: st.checkbox("(6)", key="checkbox6_state")
with col7: st.checkbox("(7)", key="checkbox7_state")
with col8: st.checkbox("(8)", key="checkbox8_state")
with col9: st.checkbox("(9)", key="checkbox9_state")