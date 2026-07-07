import subprocess
from github import Github, GithubException
from gitlab import Gitlab
import pandas as pd
import re
from pyasn1_modules.rfc8017 import emptyString
from selenium.webdriver.chrome.service import Service
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
import os
import json
import shutil
import threading
import time
from datetime import datetime
from dotenv import load_dotenv

# ── 🔑 RESTORED ALL REQUIRED UTILITY LAYER IMPORTS ────────────────────────────
import utilities.Utilities_Xpath as utils
import utilities.utils_action as action_utils
import utilities.db_utils.handler as db_handler
import utilities.TMT_Connection.Test_management_tool_utils as tmt_utils
# ──────────────────────────────────────────────────────────────────────────────

from PIL import Image
import pytesseract
import io
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI

load_dotenv()
import urllib3
import stat
import xml.etree.ElementTree as ET
import utilitymodule

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config.settings_reader import get_source, get_update_user, get_model, get_xpath_key

source = get_source()
model_type = get_model()
xpath_tag_keys = get_xpath_key()

# ------------------------------------------------------------------------------
# GLOBAL DIRECTORY PATHS AND INITIALIZATIONS
# ------------------------------------------------------------------------------
current_path = os.getcwd()
input_folder = os.path.join(current_path, "Input")
output_folder = os.path.join(current_path, "output")
Action_collection = os.path.join(output_folder, "Action_collection")
Action_collection_desktop = os.path.join(Action_collection, "Action_collection_desktop")
Page_collection = os.path.join(output_folder, "page_file_generator")
Test_case_collection = os.path.join(output_folder, "Test_Cases_collection")
Test_file_generator = os.path.join(output_folder, "test_file_generator")
feature_file_collection = os.path.join(output_folder, "Feature_file_generator")
test_data_folder = os.path.join(output_folder, "Test_data_generator")
api_template_file = os.path.join(input_folder, "Api_template.xlsx")
GIT_WORKSPACE = os.path.join(current_path, "git_test_artifacts")
JMX_FOLDER = os.path.join(current_path, "generated_jmx_files")

os.makedirs(Page_collection, exist_ok=True)
os.makedirs(Test_case_collection, exist_ok=True)
os.makedirs(Action_collection, exist_ok=True)
os.makedirs(feature_file_collection, exist_ok=True)
os.makedirs(test_data_folder, exist_ok=True)
os.makedirs(Action_collection_desktop, exist_ok=True)
os.makedirs(GIT_WORKSPACE, exist_ok=True)
os.makedirs(JMX_FOLDER, exist_ok=True)

page_screenshot_folder = os.path.join(Action_collection, "Sauce_demo")
os.makedirs(page_screenshot_folder, exist_ok=True)
os.makedirs(Test_file_generator, exist_ok=True)

st.set_page_config(
    page_title="TigerQE AI iQEA",
    page_icon="🤖",
    layout="centered"
)

for key in ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"]:
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

# Session state setup
if "page_url" not in st.session_state: st.session_state.page_url = None
if "repo_url" not in st.session_state: st.session_state.repo_url = None
if "selected_images" not in st.session_state: st.session_state.selected_images = []
if "show_popup" not in st.session_state: st.session_state.show_popup = False
if "show_form" not in st.session_state: st.session_state.show_form = False
if 'stop_monitor' not in st.session_state: st.session_state.stop_monitor = {"stop": False}
if 'monitor_thread' not in st.session_state: st.session_state.monitor_thread = None
if 'driver' not in st.session_state: st.session_state.driver = None
if 'recording_started' not in st.session_state: st.session_state.recording_started = False
if 'actions' not in st.session_state: st.session_state.actions = []
if 'selected_xpaths' not in st.session_state: st.session_state.selected_xpaths = []
if 'prompt_response' not in st.session_state: st.session_state.prompt_response = ""
if 'prompt_response_page_file' not in st.session_state: st.session_state.prompt_response_page_file = ""
if 'last_page' not in st.session_state: st.session_state.last_page = None
if 'selected_tags' not in st.session_state: st.session_state.selected_tags = ["input", "button"]
if 'selected_app' not in st.session_state: st.session_state.selected_app = []
if 'requirements_details' not in st.session_state: st.session_state.requirements_details = None
if 'accuracy_response' not in st.session_state: st.session_state.accuracy_response = None
if 'testcase_response' not in st.session_state: st.session_state.testcase_response = []
if 'scenario_response' not in st.session_state: st.session_state.scenario_response = []
if 'all_testcases' not in st.session_state: st.session_state.all_testcases = []
if 'testcase_regeneration' not in st.session_state: st.session_state.testcase_regeneration = None
if 'overall_accuracy' not in st.session_state: st.session_state.overall_accuracy = None
if "scroll_to_top" not in st.session_state: st.session_state.scroll_to_top = False
if 'workflow_text' not in st.session_state: st.session_state.workflow_text = []

for i, default_val in [(1, True), (2, False), (3, True), (4, True), (5, True), (6, True), (7, True), (8, True),
                       (9, True)]:
    if f"checkbox{i}_state" not in st.session_state:
        st.session_state[f"checkbox{i}_state"] = default_val

if "failed_files" not in st.session_state: st.session_state.failed_files = []
if "generated_jmx" not in st.session_state: st.session_state.generated_jmx = ""
if "generated_jmx_path" not in st.session_state: st.session_state.generated_jmx_path = ""


def sync_git_sparse_files(repo_url, branch, file_names, token=None):
    if not repo_url or not file_names:
        st.error("❌ Repository URL or dataset names missing.")
        return False

    def remove_readonly(func, path, excinfo):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

    try:
        clean_url = repo_url.strip()
        if not clean_url.endswith(".git"):
            clean_url += ".git"

        authenticated_url = clean_url
        if token and "github.com" in clean_url:
            authenticated_url = clean_url.replace("https://", f"https://x-access-token:{token}@")

        if os.path.exists(GIT_WORKSPACE):
            shutil.rmtree(GIT_WORKSPACE, onerror=remove_readonly)
        os.makedirs(GIT_WORKSPACE, exist_ok=True)

        # Modernized Git Sparse-Checkout initialization sequence
        subprocess.run(["git", "init"], cwd=GIT_WORKSPACE, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", authenticated_url], cwd=GIT_WORKSPACE, check=True,
                       capture_output=True)

        # Enable native sparse-checkout
        subprocess.run(["git", "sparse-checkout", "init", "--no-cone"], cwd=GIT_WORKSPACE, check=True,
                       capture_output=True)

        # Configure matching patterns for files explicitly requested
        subprocess.run(["git", "sparse-checkout", "set"] + file_names, cwd=GIT_WORKSPACE, check=True,
                       capture_output=True)

        # Attempt shallow pull
        result = subprocess.run(["git", "pull", "--depth=1", "origin", branch], cwd=GIT_WORKSPACE, capture_output=True,
                                text=True)

        # Verify if pull succeeded and actually fetched target components
        if result.returncode != 0:
            # Fallback strategy utilizing explicit fetch + checkout tracking
            subprocess.run(["git", "fetch", "--depth=1", "origin", branch], cwd=GIT_WORKSPACE, check=True,
                           capture_output=True)
            subprocess.run(["git", "checkout", f"origin/{branch}", "--"] + file_names, cwd=GIT_WORKSPACE, check=True,
                           capture_output=True)

        # Verify file existence to ensure data is inside the workspace
        downloaded_files = [f for f in os.listdir(GIT_WORKSPACE) if os.path.isfile(os.path.join(GIT_WORKSPACE, f))]
        if not downloaded_files:
            st.error(
                "❌ Git processing completed, but the specified files were not found in the branch. Verify filenames and relative path locations.")
            return False

        st.success(f"✅ Git Sparse-Sync Content Complete. Synced: {', '.join(downloaded_files)}")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        st.error(f"❌ Git CLI Operation failed: {error_msg}")
        return False
    except Exception as e:
        st.error(f"❌ Git tracking synchronization failed: {e}")
        return False


# ------------------------------------------------------------------------------
# UI RENDERING LAYOUT
# ------------------------------------------------------------------------------
st.title("🤖 TigerQE AI Platform - Performance Testing")

page_url = st.text_input(
    "Enter the URL of the page:",
    value=st.session_state.page_url if st.session_state.page_url else ""
)
st.session_state.page_url = page_url

if st.button("Open Browser"):
    if page_url:
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--remote-allow-origins=*")
        chrome_options.add_argument("--disable-dev-shm-usage")

        st.session_state.driver = webdriver.Chrome(options=chrome_options)
        st.session_state.driver.get(page_url)
        st.session_state.driver.maximize_window()
        st.success("✅ Browser opened and ready.")
else:
    if not page_url:
        st.info("ℹ️ Enter a target application URL above and launch the browser interface instance.")

# ------------------------------------------------------------------------------
# WORKFLOW RECORDER SECTIONS
# ------------------------------------------------------------------------------
if st.session_state.checkbox1_state:
    with st.expander("🔴 User Workflow Recorder"):
        option = st.radio("Choose where to record:", ('Web', 'Desktop'), key="main_recorder_choice")
        if option == 'Web':
            if not st.session_state.recording_started and st.button("🎥 Start Recording"):
                if st.session_state.driver:
                    st.session_state.actions = []
                    st.session_state.workflow_text = []
                    st.session_state.driver.execute_script(action_utils.injection_script_updated_fixed())
                    st.session_state.recording_started = True
                    st.success("Recording active...")
            if st.session_state.recording_started and st.button("🛑 Stop Recording"):
                st.session_state.actions = action_utils.get_recorded_actions(st.session_state.driver)
                st.session_state.recording_started = False
                st.success("Actions cached.")

            if st.session_state.actions:
                st.session_state.workflow_text = []
                page_name = st.text_input("Enter Page Name for Saving the Workflow:")
                if st.button("💾 Save Workflow"):
                    if not page_name:
                        st.warning("⚠ Please enter a name for the workflow.")
                    else:
                        st.session_state.workflow_text = action_utils.generate_workflow_manual(st.session_state.actions)
                        workflow_saved = False

                        if source == "database":
                            action_id = db_handler.save_action_to_db(page_name, st.session_state.workflow_text,
                                                                     get_update_user())
                            st.success(f"✅ Action saved to database (ID: {action_id})")
                            workflow_saved = True
                        elif source == "file":
                            filename = os.path.join(Action_collection, f"{page_name}_actions.txt")


                            def clean_text(s):
                                return s.replace("\u200b", "").replace("\xa0", " ").strip()


                            cleaned = [clean_text(x) for x in st.session_state.workflow_text]
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write("\n".join(cleaned))
                            st.success(f"✅ Workflow saved: {filename}")
                            st.download_button("⬇ Download Workflow", data="\n".join(st.session_state.workflow_text),
                                               file_name=f"{page_name}_actions.txt")
                            workflow_saved = True

                        if workflow_saved:
                            clear_actions = """(function() {
                                            window.__recordedActions = [];
                                            localStorage.removeItem("recordedActions");
                                        })();"""
                            st.session_state.driver.execute_script(clear_actions)
                            st.session_state.actions.clear()
                            st.session_state.workflow_text.clear()
                            st.session_state.show_popup = True
                            st.session_state.show_form = False

if st.session_state.checkbox3_state:
    with st.expander("🧮 E2E Scenario Based Test Case & JMX Generator", expanded=True):
        option = st.radio("Choose your Flow with:",
                          ('Documents', 'Recorded_Details', 'Performance Test Script (JMeter)'), key="e2e_flow_radio")

        if option == 'Performance Test Script (JMeter)':
            action_folder = Action_collection
            action_files = [f for f in os.listdir(action_folder) if f.endswith("_actions.txt")] if os.path.exists(
                action_folder) else []

            # Cleaned: Option list restricted down to local upload and AI generation
            jmx_source_mode = st.radio("Select Script Method",
                                       ["Upload Existing JMX Script File", "Generate with AI via Action File Blueprint"],
                                       index=1, horizontal=True)
            master_ip_value = "localhost"

            if jmx_source_mode == "Upload Existing JMX Script File":
                uploaded_jmx = st.file_uploader("Upload your operational target .jmx file", type=["jmx"])
                if uploaded_jmx:
                    st.session_state.generated_jmx = uploaded_jmx.getvalue().decode("utf-8")
                    st.session_state.generated_jmx_path = os.path.join(JMX_FOLDER, "runtime_api_execution.jmx")
                    with open(st.session_state.generated_jmx_path, "w", encoding="utf-8") as f: f.write(
                        st.session_state.generated_jmx)
                    st.success("📂 Script uploaded successfully.")

                st.markdown("##### 📊 Map Supporting Execution Datasets (.csv)")
                csv_source_selection = st.radio("Choose CSV Source Strategy", ["Upload CSV Datasets Locally",
                                                                               "Download CSV Datasets from Git Remote Repository"],
                                                horizontal=True)
                if csv_source_selection == "Upload CSV Datasets Locally":
                    local_csvs = st.file_uploader("Upload dataset files required by your JMX", type=["csv"],
                                                  accept_multiple_files=True)
                    if local_csvs:
                        for csv_file in local_csvs:
                            with open(os.path.join(GIT_WORKSPACE, csv_file.name), "wb") as f: f.write(
                                csv_file.getbuffer())
                        st.success("✅ Local source dataset loaded.")
                else:
                    col_g1, col_g2 = st.columns(2)
                    git_url = col_g1.text_input("Repository Remote URL",
                                                value="https://github.com/SonaJayaram/Performance_IQEAUIIntegration.git")
                    git_branch = col_g2.text_input("Target Branch / Ref", value="feature/iqea-jmeter-enhancements")
                    col_g3, col_g4 = st.columns(2)
                    git_token = col_g3.text_input("Personal Access Token", type="password")
                    target_csv_files = col_g4.text_input("Comma-Separated Dataset Names to Pull", value="data.csv")
                    if st.button("⚡ Sync Specified Git Data Components"):
                        sync_git_sparse_files(git_url, git_branch,
                                              [f.strip() for f in target_csv_files.split(",") if f.strip()], git_token)

            elif jmx_source_mode == "Generate with AI via Action File Blueprint":
                if not action_files:
                    st.warning("⚠ No recorded workflow action logs found in workspace.")
                else:
                    selected_action_file = st.selectbox("Select Recorded Workflow Profile", options=action_files)
                    with open(os.path.join(action_folder, selected_action_file), "r", encoding="utf-8") as f:
                        actions_lines = f.read()
                    ai_prompt = st.text_area("Enter Additional Performance Test Settings",
                                             value="Generate Jmeter compatible jmx script with 10 users, 5 seconds rampup, 10 loops and 120 seconds test duration")

                    if st.button("🚀 Generate AI-based JMX"):
                        user_prompt = f"Generate complete valid executable JMeter 5.5 structure for following workflows:\n{actions_lines}\n\nAdditional parameters:\n{ai_prompt}"
                        with st.spinner("Calling Core LLM Orchestrator via proxy paths..."):
                            raw_ai = utilitymodule.get_output_from_ai(user_prompt)
                            if raw_ai is None:
                                st.error("❌ JMX generation failed. Machine blocked or VNet network peering mismatch.")
                            else:
                                ai_config = utilitymodule.extract_ai_test_config(ai_prompt, raw_ai)
                                st.session_state.generated_jmx = utilitymodule.update_jmx_file(raw_ai.strip(),
                                                                                               ai_config)
                                st.session_state.generated_jmx_path = os.path.join(JMX_FOLDER,
                                                                                   f"{selected_action_file.replace('_actions.txt', '')}.jmx")
                                with open(st.session_state.generated_jmx_path, "w", encoding="utf-8") as f:
                                    f.write(st.session_state.generated_jmx)
                                st.success("✅ JMX generated successfully!")

            if st.session_state.generated_jmx:
                st.subheader("📄 Generated JMX Blueprint Output")
                st.code(st.session_state.generated_jmx, language="xml")

                target_download_filename = os.path.basename(
                    st.session_state.generated_jmx_path) if st.session_state.generated_jmx_path else "api_performance_plan.jmx"
                st.download_button(
                    label=f"⬇ Download Plan ({target_num_threads if 'target_num_threads' in locals() else 'Custom'} Profiles)",
                    data=st.session_state.generated_jmx,
                    file_name=target_download_filename,
                    mime="application/xml",
                    key="performance_jmx_downloader_widget"
                )

        elif option == 'Documents':
            pass

if st.session_state.checkbox9_state:
    with st.expander("🚀 Active Test Execution & Realtime Telemetry Monitoring Console", expanded=True):
        st.title("Execute Generated Test Scripts and View Html Reports")

        jmeter_path = st.text_input(
            "JMeter Executable Path/Command",
            value=r"F:\Sona_Performance\apache-jmeter-5.6.3\apache-jmeter-5.6.3\bin\jmeter.bat",
            key="execution_jmeter_path"
        )

        saved_jmx_files = []
        if os.path.exists("generated_jmx_files"):
            saved_jmx_files = [f for f in os.listdir("generated_jmx_files") if f.endswith(".jmx")]

        default_index = 0
        if st.session_state.get("generated_jmx_path"):
            filename_only = os.path.basename(st.session_state.generated_jmx_path)
            if filename_only in saved_jmx_files:
                default_index = saved_jmx_files.index(filename_only)

        selected_file = st.selectbox("Select Test Script to Execute", saved_jmx_files, index=default_index,
                                     key="sb_execution_target")

        if selected_file:
            st.markdown("##### ⚙️ Overriding Target Execution Runtime Properties")
            col_u1, col_u2, col_u3, col_u4 = st.columns(4)

            target_num_threads = col_u1.number_input("Concurrent Users (Threads)", min_value=1, value=10, step=1)
            target_ramp_time = col_u2.number_input("Ramp-Up Period (Seconds)", min_value=1, value=5, step=1)
            target_loop_count = col_u3.number_input("Loop Interations (-1 for Infinite)", min_value=-1, value=-1,
                                                    step=1)
            target_duration_time = col_u4.number_input("Test Run Schedule (Seconds)", min_value=1, value=120, step=1)

            execution_profile = st.selectbox("Choose Environment Infrastructure Config",
                                             ["Local Dry Run / Smoke Test (Your Machine Only)",
                                              "Actual Load Test (Distributed Master-Slave Config)"],
                                             key="exec_env_matrix")

            if "Actual Load Test" in execution_profile:
                local_master_ip = st.text_input("Master VM Infrastructure IP", value="10.0.0.4",
                                                key="runtime_master_ip_input")
                master_ip_value = local_master_ip if local_master_ip else "10.0.0.4"
            else:
                master_ip_value = "localhost"

            # ── 📊 INTEGRATED LIVE TELEMETRY METRIC REDIRECTION ────────────────
            st.write("---")
            st.markdown("### 📊 Live Telemetry Metric Redirection")

            grafana_url = st.text_input(
                "Your Grafana Dashboard URL",
                value="http://localhost:3000/d/adf2bsx/iqeadashboard?orgId=1&refresh=5s&panelId=1",
                key="grafana_dashboard_url_input"
            )

            # Stylized full-width purple redirect button using markdown
            st.markdown(
                f"""
                <a href="{grafana_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #800080; color: white; text-align: center; 
                                padding: 10px; border-radius: 5px; font-weight: bold; 
                                font-size: 16px; margin-bottom: 15px; cursor: pointer;">
                        📈 Open Live Grafana Monitor Dashboard
                    </div>
                </a>
                """,
                unsafe_allow_html=True
            )

            # Unified Orchestration and Execution Trigger button
            if st.button("🚀 Fire Performance Execution Plan", key="btn_fire_performance_plan"):
                st.info("Initiating orchestration pipeline and running target test context configuration...")
                jmx_full_path = os.path.join("generated_jmx_files", selected_file)

                if not os.path.exists(jmx_full_path):
                    st.error(f"❌ Selected file layout error: {selected_file} not found locally.")
                else:
                    with open(jmx_full_path, "r", encoding="utf-8") as f:
                        original_jmx = f.read()

                    base_name = os.path.splitext(selected_file)[0]

                    ai_config = {
                        "threads": int(target_num_threads),
                        "rampup": int(target_ramp_time),
                        "loops": int(target_loop_count),
                        "duration": int(target_duration_time)
                    }

                    st.subheader("📋 Active Runtime Configuration Map")
                    st.json(ai_config)

                    updated_jmx = utilitymodule.update_jmx_file(original_jmx, ai_config)
                    updated_jmx = updated_jmx.replace("localhost:8086", f"{master_ip_value}:8086")

                    try:
                        root_xml = ET.fromstring(updated_jmx)
                        for element in root_xml.iter("CSVDataSet"):
                            for prop in element.iter("stringProp"):
                                if prop.attrib.get("name") == "filename":
                                    prop.text = os.path.join(GIT_WORKSPACE, os.path.basename(prop.text)).replace("\\", "/")
                        updated_jmx = ET.tostring(root_xml, encoding="utf-8").decode("utf-8")
                    except Exception:
                        pass

                    with open(jmx_full_path, "w", encoding="utf-8") as f:
                        f.write(updated_jmx)

                    report_base_dir = os.path.join(current_path, "jmeter_reports", base_name)
                    output_jtl = os.path.join(report_base_dir, f"{base_name}_log.jtl")
                    html_report_dir = os.path.join(report_base_dir, "html_dashboard")

                    if os.path.exists(report_base_dir): shutil.rmtree(report_base_dir, ignore_errors=True)
                    os.makedirs(report_base_dir, exist_ok=True)

                    command = [jmeter_path, "-n", "-t", jmx_full_path, "-l", output_jtl, "-Jsummariser.name=summary"]
                    if execution_profile != "Local Dry Run / Smoke Test (Your Machine Only)":
                        command += ["-R", "10.0.0.5:1099"]

                    st.subheader("📺 Live JMeter Console Stream")
                    log_stdout_box = st.empty()
                    accumulated_logs = ""

                    jmeter_bin_directory = os.path.dirname(jmeter_path)
                    custom_env = os.environ.copy()
                    if jmeter_bin_directory: custom_env["JMETER_HOME"] = os.path.dirname(jmeter_bin_directory)
                    custom_env[
                        "JVM_ARGS"] = f"-Djava.rmi.server.hostname={master_ip_value} -Dclient.rmi.localport=60000 -Dserver.rmi.ssl.disable=true"

                    try:
                        process = subprocess.Popen(command, shell=True, env=custom_env, cwd=current_path,
                                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        start_time = datetime.now()
                        max_allowed_seconds = int(target_duration_time) + 60

                        while True:
                            line = process.stdout.readline()
                            if line:
                                accumulated_logs += line
                                log_stdout_box.code(accumulated_logs[-3000:])
                            if not line and process.poll() is not None: break

                            if (datetime.now() - start_time).total_seconds() > max_allowed_seconds:
                                st.warning("⚠️ Workload timeframe window hit. Gracefully finalizing files...")
                                break

                        if process.poll() is None:
                            subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True, stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL)
                        process.wait()
                        time.sleep(3)

                        if os.path.exists(output_jtl) and os.path.getsize(output_jtl) > 100:
                            try:
                                with open(output_jtl, "r", encoding="utf-8", errors="ignore") as f:
                                    lines = f.readlines()
                                if lines and len(lines[-1].split(',')) < len(lines[0].split(',')):
                                    with open(output_jtl, "w", encoding="utf-8") as f: f.writelines(lines[:-1])
                                    st.caption("🔧 Sanitized trailing line formatting mismatch artifacts.")
                            except Exception:
                                pass

                            if os.path.exists(html_report_dir): shutil.rmtree(html_report_dir, ignore_errors=True)

                            st.info("📊 Generating JMeter HTML Dashboard Assets...")
                            report_process = subprocess.run([jmeter_path, "-g", output_jtl, "-o", html_report_dir],
                                                            shell=True, cwd=jmeter_bin_directory, env=custom_env,
                                                            capture_output=True, text=True)

                            if report_process.returncode == 0:
                                st.success("✅ HTML Report generated successfully.")
                                st.info(f"📊 Dashboard Location: {html_report_dir}")
                            else:
                                st.error("❌ HTML Report compilation sequence encountered warnings.")
                        else:
                            st.error("❌ Log data was empty.")

                    except Exception as ex:
                        st.error(f"❌ Core engine configuration crash: {ex}")
# ──────────────────────────────────────────────────────────────────────────────

st.divider()
st.markdown("### Contact Us\n- Reach us at [QE Core Team](mailto:sahil.gupta@tigeranalytics.com)")