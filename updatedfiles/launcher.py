import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
import threading
import tempfile

import sys
import os
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities import utils_action as action_utils
import utilities.Utilities_Xpath as utils
import desktop

import utilitymodule
from desktop.recorder import DesktopRecorder
from desktop.session import DesktopSession

current_path = os.getcwd()
from config.settings_reader import get_source, get_update_user, get_model, get_xpath_key

page_screenshot_folder = os.path.join(current_path, "demofolder")
Action_collection = os.path.join(current_path, "actions_workspaces")
Action_collection_desktop = os.path.join(Action_collection, "Action_collection_desktop")
source = get_source()
if "actions" not in st.session_state:
    st.session_state.actions = []

if "workflow_text" not in st.session_state:
    st.session_state.workflow_text = []

if "recording_started" not in st.session_state:
    st.session_state.recording_started = False

if "monitor_threads" not in st.session_state:
    st.session_state.monitor_threads = []

if "stop_monitor" not in st.session_state:
    st.session_state.stop_monitor = {"stop": False}

if "injected_windows" not in st.session_state:
    st.session_state.injected_windows = {}

if "last_urls" not in st.session_state:
    st.session_state.last_urls = {}

if "current_window_ref" not in st.session_state:
    st.session_state.current_window_ref = {"handle": None}

# ---------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------
st.set_page_config(
    page_title="TigerQE AI iQEA",
    page_icon="",
    layout="centered"
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
    "monitor_threads": []
}

for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------
st.title(" 🤖 TigerQE AI Platform - Performance Testing")

# ---------------------------------------------------
# OPEN BROWSER SECTION
# ---------------------------------------------------
page_url = st.text_input("Enter the URL of the page:")

if st.button("Open Browser"):
    if not page_url.strip():
        st.error("Please enter a valid URL.")
    else:
        try:
            # 1. Setup Options
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--remote-allow-origins=*")

            # 2. Launch Chrome ONCE and store it immediately
            driver = webdriver.Chrome(options=chrome_options)
            st.session_state.driver = driver

            # 3. Navigate and Wait
            st.session_state.driver.get(page_url)

            # Using your utility module or standard waiter
            WebDriverWait(st.session_state.driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            st.success(f"✅ Browser opened successfully: {page_url}")

        except Exception as e:
            st.error(f"❌ Failed to open browser: {e}")

# ---------------------------------------------------
# JMX SCRIPT GENERATOR
# ---------------------------------------------------


# Folder to save generated JMX files
JMX_FOLDER = "generated_jmx_files"
os.makedirs(JMX_FOLDER, exist_ok=True)

if "generated_jmx" not in st.session_state:
    st.session_state.generated_jmx = ""

if "generated_jmx_path" not in st.session_state:
    st.session_state.generated_jmx_path = ""

if st.session_state.checkbox5_state:

    with st.expander("🔎 JMX script generator "):

        st.title("JMX using prompt")

        st.markdown("Enter your prompt for generating a JMeter (.jmx) script.")

        # Optional script name
        script_name = st.text_input(
            "Enter JMX File Name",
            value="generated_test_plan"
        )

        user_prompt = st.text_area(
            "Enter Prompt",
            height=300,
            max_chars=5000,
            placeholder="""
Example:

Generate a JMeter JMX script for:
1. Login API
2. Search product API
3. Add to cart API
4. Validate response codes
5. Add assertions
6. Add CSV data config
7. Add thread group with 50 users
"""
        )

        # ---------------------------------------------------
        # GENERATE BUTTON
        # ---------------------------------------------------
        if st.button("Generate JMX Script"):

            if not user_prompt.strip():
                st.error("Please enter a prompt.")

            else:
                with st.spinner("Generating JMX Script..."):

                    try:
                        response = utilitymodule.get_output_from_ai(user_prompt)

                        # Validate AI response
                        if response is None:
                            st.error("❌ AI did not return any response.")
                        else:

                            # Convert to string if needed
                            response = str(response)

                            # Store in session
                            st.session_state.generated_jmx = response

                            # Create full file path
                            file_name = f"{script_name}.jmx"
                            file_path = os.path.join(JMX_FOLDER, file_name)

                            # Save locally
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(response)

                            # Store path
                            st.session_state.generated_jmx_path = file_path

                            st.success("✅ JMX generated and saved successfully.")

                            st.info(f"Saved Location: {file_path}")
                    except Exception as e:
                        st.error(f"❌ Error generating JMX: {e}")

        # ---------------------------------------------------
        # DISPLAY GENERATED JMX
        # ---------------------------------------------------
        if st.session_state.generated_jmx:
            st.subheader("Generated JMX Script")

            st.text_area(
                "JMX Output",
                value=st.session_state.generated_jmx,
                height=400
            )

            # Download button
            st.download_button(
                label="⬇ Download JMX File",
                data=st.session_state.generated_jmx,
                file_name=f"{script_name}.jmx",
                mime="application/xml"
            )

        # ---------------------------------------------------
        # SHOW SAVED FILES
        # ---------------------------------------------------
        st.markdown("---")
        st.subheader("Saved JMX Scripts")

        saved_files = [
            f for f in os.listdir(JMX_FOLDER)
            if f.endswith(".jmx")
        ]

        if saved_files:
            selected_saved_file = st.selectbox(
                "Select Saved JMX File",
                saved_files
            )

            selected_file_path = os.path.join(
                JMX_FOLDER,
                selected_saved_file
            )

            st.success(f"Selected File: {selected_saved_file}")

            # Reuse later during execution
            st.session_state.generated_jmx_path = selected_file_path

        else:
            st.info("No saved JMX scripts found.")

# ---------------------------------------------------
# USER WORKFLOW RECORDER
# ---------------------------------------------------
if st.session_state.checkbox1_state:

    with st.expander("🔴 User Workflow Recorder", expanded=True):

        option = st.radio(
            "Choose where to record:",
            ("Web", "Desktop")
        )

        # =====================================================
        # WEB RECORDING
        # =====================================================

        if option == "Web":

            st.subheader(
                "Record User Actions & Capture Screenshots of User Navigation"
            )

            # =====================================
            # START RECORDING
            # =====================================

            if (
                not st.session_state.recording_started
                and st.button("🎥 Start Recording")
            ):

                try:

                    driver = st.session_state.driver

                    if not driver:
                        st.error("Driver not initialized.")
                        st.stop()

                    # ---------------------------------
                    # CLEAR PREVIOUS DATA
                    # ---------------------------------

                    st.session_state.actions.clear()
                    st.session_state.workflow_text.clear()

                    # ---------------------------------
                    # STOP OLD THREADS
                    # ---------------------------------

                    st.session_state.stop_monitor["stop"] = True

                    for t in st.session_state.monitor_threads:
                        if t and t.is_alive():
                            t.join(timeout=2)

                    # ---------------------------------
                    # RESET STATE
                    # ---------------------------------

                    st.session_state.stop_monitor = {"stop": False}
                    st.session_state.monitor_threads = []
                    st.session_state.injected_windows = {}
                    st.session_state.last_urls = {}
                    st.session_state.current_window_ref = {
                        "handle": driver.current_window_handle
                    }

                    # ---------------------------------
                    # INJECT JAVASCRIPT
                    # ---------------------------------

                    driver.execute_script(
                        action_utils.injection_script_updated_fixed()
                    )

                    current_handle = driver.current_window_handle

                    st.session_state.injected_windows[current_handle] = True

                    print(
                        f"✅ JS injected into window: "
                        f"{current_handle}"
                    )

                    # =====================================
                    # THREAD 1 - NEW WINDOW CHECKER
                    # =====================================

                    t1 = threading.Thread(
                        target=utils.thread_new_window_checker,
                        args=(
                            driver,
                            st.session_state.injected_windows,
                            st.session_state.last_urls,
                            st.session_state.stop_monitor,
                            page_screenshot_folder,
                            st.session_state.current_window_ref
                        ),
                        daemon=True
                    )

                    # =====================================
                    # THREAD 2 - URL + FOCUS MONITOR
                    # =====================================

                    t2 = threading.Thread(
                        target=utils.thread_focus_and_url_monitor,
                        args=(
                            driver,
                            st.session_state.injected_windows,
                            st.session_state.last_urls,
                            st.session_state.stop_monitor,
                            page_screenshot_folder,
                            st.session_state.current_window_ref
                        ),
                        daemon=True
                    )

                    # =====================================
                    # THREAD 3 - SCREENSHOT CAPTURE
                    # =====================================

                    t3 = threading.Thread(
                        target=utils.thread_focus_screenshot,
                        args=(
                            driver,
                            st.session_state.stop_monitor,
                            page_screenshot_folder,
                            source
                        ),
                        daemon=True
                    )

                    # =====================================
                    # THREAD 4 - REINJECT CHECK
                    # =====================================

                    t4 = threading.Thread(
                        target=utils.thread_reinject_action_check,
                        args=(
                            driver,
                            st.session_state.stop_monitor,
                            st.session_state.last_urls,
                            st.session_state.current_window_ref,
                            st.session_state.injected_windows
                        ),
                        daemon=True
                    )

                    # =====================================
                    # START THREADS
                    # =====================================

                    t1.start()
                    t2.start()
                    t3.start()
                    t4.start()

                    st.session_state.monitor_threads = [
                        t1,
                        t2,
                        t3,
                        t4
                    ]

                    st.session_state.recording_started = True

                    st.success(
                        "✅ Recording started. "
                        "Interact with the browser."
                    )

                except Exception as e:
                    st.error(f"Start recording failed: {e}")

            # =====================================
            # STOP RECORDING
            # =====================================

            if (
                st.session_state.recording_started
                and st.button("🛑 Stop Recording")
            ):

                try:

                    driver = st.session_state.driver

                    # ---------------------------------
                    # FETCH ACTIONS
                    # ---------------------------------

                    recorded_actions = (
                        action_utils.get_recorded_actions(driver)
                    )

                    if recorded_actions:

                        for act in recorded_actions:

                            if act not in st.session_state.actions:
                                st.session_state.actions.append(act)

                    # ---------------------------------
                    # STOP THREADS
                    # ---------------------------------

                    st.session_state.stop_monitor["stop"] = True

                    for t in st.session_state.monitor_threads:
                        if t and t.is_alive():
                            t.join(timeout=2)

                    st.session_state.monitor_threads = []

                    st.session_state.recording_started = False

                    st.success(
                        f"✅ Recording stopped. "
                        f"{len(st.session_state.actions)} "
                        f"actions captured."
                    )

                except Exception as e:
                    st.error(f"Stop recording failed: {e}")

            # =====================================
            # SHOW ACTIONS
            # =====================================

            if st.session_state.actions:

                st.subheader("Captured Actions")

                for idx, action in enumerate(
                    st.session_state.actions,
                    start=1
                ):
                    st.write(f"{idx}. {action}")

                # =====================================
                # SAVE WORKFLOW
                # =====================================

                page_name = st.text_input(
                    "Enter workflow name:"
                )

                if st.button("💾 Save Workflow"):

                    try:

                        if not page_name.strip():
                            st.warning(
                                "⚠ Please enter workflow name."
                            )
                            st.stop()

                        # ---------------------------------
                        # GENERATE WORKFLOW TEXT
                        # ---------------------------------

                        workflow_text = (
                            action_utils.generate_workflow_manual(
                                st.session_state.actions
                            )
                        )

                        # ---------------------------------
                        # CLEAN TEXT
                        # ---------------------------------

                        def clean_text(s):
                            return (
                                s.replace("\u200b", "")
                                .replace("\xa0", " ")
                                .strip()
                            )

                        cleaned = [
                            clean_text(x)
                            for x in workflow_text
                        ]

                        # ---------------------------------
                        # SAVE FILE
                        # ---------------------------------

                        filename = os.path.join(
                            Action_collection,
                            f"{page_name}_actions.txt"
                        )

                        with open(
                            filename,
                            "w",
                            encoding="utf-8"
                        ) as f:
                            f.write("\n".join(cleaned))

                        st.success(
                            f"✅ Workflow saved successfully:\n"
                            f"{filename}"
                        )

                        # ---------------------------------
                        # DOWNLOAD BUTTON
                        # ---------------------------------

                        st.download_button(
                            "⬇ Download Workflow",
                            data="\n".join(cleaned),
                            file_name=f"{page_name}_actions.txt",
                            mime="text/plain"
                        )

                        # ---------------------------------
                        # CLEAR BROWSER STORAGE
                        # ---------------------------------

                        clear_actions = """
                        (function() {

                            window.__recordedActions = [];

                            localStorage.removeItem(
                                "recordedActions"
                            );

                            console.log(
                                "🧹 Cleared recorded actions"
                            );

                        })();
                        """

                        st.session_state.driver.execute_script(
                            clear_actions
                        )

                    except Exception as e:
                        st.error(f"Save failed: {e}")
# ============================================================
# PERFORMANCE TEST SCRIPT GENERATOR
# ============================================================
if st.session_state.checkbox3_state:
    with st.expander("🧮 Performance Test Script Generator"):
        st.title("Performance Test Script Generator")
        # ====================================================
        # ACTIONS FOLDER
        # ====================================================
        action_folder = Action_collection

        if not os.path.exists(action_folder):
            st.error("❌ Actions folder not found.")
            st.stop()
        # ====================================================
        # GET RECORDED ACTION FILES
        # ====================================================
        action_files = [
            f for f in os.listdir(action_folder)
            if f.endswith("_actions.txt")
        ]

        if not action_files:
            st.warning("⚠ No recorded workflow files found.")
            st.stop()

        # ====================================================
        # SELECT WORKFLOW
        # ====================================================

        selected_action_file = st.selectbox(
            "Select Recorded Workflow",
            options=action_files
        )

        selected_file_path = os.path.join(
            action_folder,
            selected_action_file
        )

        # ====================================================
        # LOAD ACTIONS
        # ====================================================

        try:
            with open(
                selected_file_path,
                "r",
                encoding="utf-8"
            ) as f:

                actions = [
                    line.strip()
                    for line in f.readlines()
                    if line.strip()
                ]

        except Exception as e:
            st.error(f"❌ Failed to read action file:\n{e}")
            st.stop()

        # ====================================================
        # DISPLAY ACTIONS
        # ====================================================

        st.subheader("📋 Recorded Browser Actions")

        for idx, action in enumerate(actions, start=1):
            st.write(f"{idx}. {action}")

        # ====================================================
        # ADDITIONAL REQUIREMENTS
        # ====================================================

        st.subheader("🤖 AI-based JMX Generation")

        ai_prompt = st.text_area(
            "Enter Additional Performance Test Requirements",
            placeholder="""
Example:
- Generate JMeter JMX
- Add 100 users
- Ramp-up time 30 seconds
- Add Assertions
- Add Think Time
- Add Cookie Manager
- Add CSV Data Set Config
- Add Listeners
            """,
            height=200
        )

        # ====================================================
        # GENERATE JMX USING AI
        # ====================================================

        if st.button("🚀 Generate AI-based JMX"):

            try:

                # ------------------------------------------------
                # WORKFLOW NAME
                # ------------------------------------------------

                workflow_name = (
                    selected_action_file
                    .replace("_actions.txt", "")
                )

                # ------------------------------------------------
                # CONVERT ACTIONS TO CLEAN TEXT
                # ------------------------------------------------

                formatted_actions = "\n".join(
                    [
                        f"{idx+1}. {action}"
                        for idx, action in enumerate(actions)
                    ]
                )

                # ------------------------------------------------
                # BUILD AI PROMPT
                # ------------------------------------------------

                user_prompt = f"""
You are an expert JMeter Performance Test Engineer.

Convert the following recorded browser workflow actions into a valid Apache JMeter .jmx test plan.

Requirements:
1. Generate valid JMX XML only.
2. Include:
    - Test Plan
    - Thread Group
    - HTTP Request Samplers
    - Cookie Manager
    - Header Manager
    - Think Time Timers where appropriate
    - Assertions if applicable
3. Maintain the exact navigation flow.
4. Infer HTTP methods based on actions.
5. Use realistic sampler names.
6. Ensure generated XML is importable into JMeter.
7. Do not provide explanation.
8. Return only XML.

Recorded Browser Actions:
{formatted_actions}

Additional Performance Requirements:
{ai_prompt}
"""

                # ------------------------------------------------
                # DEBUG VIEW
                # ------------------------------------------------

                with st.expander("📝 Generated AI Prompt"):
                    st.code(user_prompt)

                # ------------------------------------------------
                # AI API CALL
                # ------------------------------------------------

                with st.spinner("🤖 AI is generating JMX..."):

                    response = utilitymodule.get_output_from_ai(
                        user_prompt
                    )

                # ------------------------------------------------
                # VALIDATE RESPONSE
                # ------------------------------------------------

                if not response:
                    st.error("❌ Empty response received from AI.")
                    st.stop()

                generated_jmx = response.strip()

                # ------------------------------------------------
                # SHOW GENERATED OUTPUT
                # ------------------------------------------------

                st.subheader("📄 Generated JMX")

                st.code(
                    generated_jmx,
                    language="xml"
                )

                # ------------------------------------------------
                # SAVE GENERATED JMX
                # ------------------------------------------------

                jmx_output_folder = os.path.join(
                    os.getcwd(),
                    "generated_jmx_files"
                )

                os.makedirs(
                    jmx_output_folder,
                    exist_ok=True
                )

                jmx_filename = os.path.join(
                    jmx_output_folder,
                    f"{workflow_name}.jmx"
                )

                with open(
                    jmx_filename,
                    "w",
                    encoding="utf-8"
                ) as f:

                    f.write(generated_jmx)

                # ------------------------------------------------
                # SUCCESS
                # ------------------------------------------------

                st.success(
                    f"✅ JMX generated successfully:\n"
                    f"{jmx_filename}"
                )

                # ------------------------------------------------
                # DOWNLOAD BUTTON
                # ------------------------------------------------

                st.download_button(
                    label="⬇ Download JMX File",
                    data=generated_jmx,
                    file_name=f"{workflow_name}.jmx",
                    mime="application/xml"
                )

            except Exception as e:

                st.error(
                    f"❌ Failed to generate JMX:\n{e}"
                )

# ---------------------------------------------------
# TEST EXECUTION & REPORT
# ---------------------------------------------------
if st.session_state.checkbox9_state:

    with st.expander("🚀 Test Execution & Html Report"):

        st.title("Execute Generated Test Scripts and View Html Reports")

        # Configurations for local JMeter location
        jmeter_path = st.text_input(
            "JMeter Executable Path/Command",
            value="jmeter",
            help="Change to complete path if 'jmeter' is not in environment PATH (e.g., C:\\apache-jmeter\\bin\\jmeter.bat)"
        )

        # Dynamic population from JMX folder
        saved_jmx_files = []
        if os.path.exists(JMX_FOLDER):
            saved_jmx_files = [f for f in os.listdir(JMX_FOLDER) if f.endswith(".jmx")]

        if not saved_jmx_files:
            saved_jmx_files = ["Sample1.jmx", "Sample2.jmx"]

        selected_file = st.selectbox(
            "Select Test Script to Execute",
            saved_jmx_files
        )

        if selected_file:
            # =================================================
            # AI PROMPT INPUT
            # =================================================

            ai_execution_prompt = st.text_area(
                "🤖 AI JMeter Execution Instructions",
                height=180,
                placeholder="""
                    Examples:
            
                    - Run smoke test with 2 users
                    - Ramp from 1 to 100 users over 5 minutes
                    - Execute spike test with 500 users
                    - Run soak test for 1 hour
                    - Gradually increase load every 30 seconds
                    - Execute with infinite loops for 10 mins
                                    """
                        )

            # =================================================
            # RUN TEST BUTTON
            # =================================================

        if st.button("Run Test Script"):
            jmx_full_path = os.path.join(JMX_FOLDER, selected_file)

            if not os.path.exists(jmx_full_path):
                st.error(f"❌ Selected file layout error: {selected_file} not found locally in {JMX_FOLDER}.")
            else:
                # Set up directory parameters for logs & HTML reports
                with open(
                        jmx_full_path,
                        "r",
                        encoding="utf-8"
                ) as f:

                    original_jmx = f.read()
                base_name = os.path.splitext(selected_file)[0]
                with st.spinner("🤖 AI analyzing execution instructions..."):

                    ai_config = utilitymodule.extract_ai_test_config(
                        ai_execution_prompt,
                        original_jmx
                    )

                st.subheader("📋 AI Generated Execution Config")
                st.json(ai_config)
                report_base_dir = os.path.join(current_path, "jmeter_reports", base_name)


                # =========================================
                # UPDATE JMX
                # =========================================

                updated_jmx = utilitymodule.update_jmx_file(
                    original_jmx,
                    ai_config
                )

                # =========================================
                # VALIDATE XML
                # =========================================

                valid, error = utilitymodule.validate_jmx(updated_jmx)
                if not valid:
                    st.error(f"❌ Invalid JMX generated: {error}")
                    st.stop()

                st.success("✅ Updated JMX validated successfully")
                # =========================================
                # SAVE TEMP UPDATED JMX
                # =========================================

                temp_dir = tempfile.gettempdir()

                updated_test_path = os.path.join(
                    temp_dir,
                    f"updated_{selected_file}"
                )

                with open(
                        updated_test_path,
                        "w",
                        encoding="utf-8"
                ) as f:

                    f.write(updated_jmx)
                print("##### updated test path ", updated_test_path)
                st.success("✅ Temporary updated JMX created")
                report_base_dir = os.path.join(current_path, "jmeter_reports", base_name)

                output_jtl = os.path.join(report_base_dir, f"{base_name}_log.jtl")
                html_report_dir = os.path.join(report_base_dir, "html_dashboard")
                # Generate dynamic command strings for non-GUI execution
                command = [
                    jmeter_path,
                    "-n",
                    "-t", updated_test_path,
                    "-l", output_jtl,
                    "-e", "-o", html_report_dir,
                    "-Jsummariser.name=summary"
                ]

                with st.spinner("Executing JMeter Script Engine and compiling outputs..."):
                    try:
                        # Clear old run properties if re-executing
                        if os.path.exists(output_jtl):
                            os.remove(output_jtl)
                        if os.path.exists(html_report_dir):
                            import shutil

                            shutil.rmtree(html_report_dir)

                        result = subprocess.run(command, capture_output=True, text=True, check=True)

                        st.success("✅ JMeter engine completed execution cycle successfully!")
                        print("#### jmeter engine completed the execution cycle and report is ready !!")
                        st.info(f"📁 **Logs Destination (.jtl):** {output_jtl}")
                        st.info(f"📊 **HTML Dashboard Directory:** {html_report_dir}")

                        with st.expander("Show Console Outputs Log"):
                            st.code(result.stdout)

                    except subprocess.CalledProcessError as err:
                        st.error("❌ Thread execution failure occurred inside JMeter runtime.")
                        st.code(err.stderr if err.stderr else err.stdout)
                    except Exception as ex:
                        st.error(f"❌ Failed to coordinate script execution thread: {ex}")

        if st.button("View Allure Report"):
            st.success("Allure report functionality will be added here.")

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------
st.divider()

st.markdown("""
### Contact Us
- Reach us at [QE Core Team](mailto:sahil.gupta@tigeranalytics.com)
""")

# ---------------------------------------------------
# CHECKBOX DISPLAY SECTION
# ---------------------------------------------------
col0, col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(10)

with col0:
    st.write("Choose display")

with col1:
    st.checkbox("(1)", key="checkbox1_state")

with col2:
    st.checkbox("(2)", key="checkbox2_state")

with col3:
    st.checkbox("(3)", key="checkbox3_state")

with col4:
    st.checkbox("(4)", key="checkbox4_state")

with col5:
    st.checkbox("(5)", key="checkbox5_state")

with col6:
    st.checkbox("(6)", key="checkbox6_state")

with col7:
    st.checkbox("(7)", key="checkbox7_state")

with col8:
    st.checkbox("(8)", key="checkbox8_state")

with col9:
    st.checkbox("(9)", key="checkbox9_state")