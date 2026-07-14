import subprocess
from github import Github, GithubException  # Make sure GithubException is imported
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
from desktop.session import *
from desktop.recorder import *
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
session_states = {
    "page_url": None, "repo_url": None, "selected_images": [], "show_popup": False, "show_form": False,
    "stop_monitor": {"stop": False}, "monitor_thread": None, "driver": None, "recording_started": False,
    "actions": [], "selected_xpaths": [], "prompt_response": "", "prompt_response_page_file": "",
    "last_page": None, "selected_tags": ["input", "button"], "selected_app": [], "requirements_details": None,
    "accuracy_response": None, "testcase_response": [], "scenario_response": [], "all_testcases": [],
    "testcase_regeneration": None, "overall_accuracy": None, "scroll_to_top": False, "workflow_text": [],
    "checkbox1_state": True, "checkbox2_state": False, "checkbox3_state": True, "checkbox4_state": True,
    "checkbox5_state": True, "checkbox6_state": True, "checkbox7_state": True, "checkbox8_state": True,
    "checkbox9_state": True, "failed_files": [], "regenerate_clicked": False, "save_testcases": False,
    "save_regenerated_testcases": False, "generated_test_script": None, "script_gen_inputs": {},
    "script_editor_version": 0, "injected_windows": {}, "workflow_text_desktop": [], "xpath_for_new_page": False,
    "xpath_for_new_page_user_info": False, "recorded_script": None, "recorded_script_language": "Python-Selenium",
    "rb_actions_snapshot": [], "open_expander_collection": False, "recorded_actions_history": False,
    "tmt_tool": "None", "tmt_connected": False, "tmt_existing_tcs": [], "tmt_selected_plan_id": None,
    "tmt_selected_suite_id": None, "tmt_plans": [], "tmt_suites": [], "gap_analysis_result": None,
    "tmt_jira_project_key": "", "tmt_fetch_type": "Test Cases", "tmt_gap_approved": False,
    "tmt_replacement_responses": [], "tmt_deletion_notice": [], "tmt_gen_inputs": {},
    "document_source_selector": "Files", "uploaded_file_path": None, "azure_workitem_id": "",
    "jira_workitem_id": "", "excel_path": "", "test_data_action_data": "", "test_files_content": "",
    "test_data_addition_info": "", "test_data_llm_response": "", "api_data": "", "select_all": False,
    "desktop_action_name": "", "recorder": DesktopRecorder(), "generated_jmx": "", "generated_jmx_path": ""
}

for key, default_val in session_states.items():
    if key not in st.session_state:
        st.session_state[key] = default_val


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
        if not clean_url.endswith(".git"): clean_url += ".git"
        authenticated_url = clean_url
        if token and "github.com" in clean_url:
            authenticated_url = clean_url.replace("https://", f"https://x-access-token:{token}@")
        if os.path.exists(GIT_WORKSPACE):
            shutil.rmtree(GIT_WORKSPACE, onerror=remove_readonly)
        os.makedirs(GIT_WORKSPACE, exist_ok=True)
        subprocess.run(["git", "init"], cwd=GIT_WORKSPACE, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", authenticated_url], cwd=GIT_WORKSPACE, check=True,
                       capture_output=True)
        subprocess.run(["git", "sparse-checkout", "init", "--no-cone"], cwd=GIT_WORKSPACE, check=True,
                       capture_output=True)
        subprocess.run(["git", "sparse-checkout", "set"] + file_names, cwd=GIT_WORKSPACE, check=True,
                       capture_output=True)
        result = subprocess.run(["git", "pull", "--depth=1", "origin", branch], cwd=GIT_WORKSPACE, capture_output=True,
                                text=True)
        if result.returncode != 0:
            subprocess.run(["git", "fetch", "--depth=1", "origin", branch], cwd=GIT_WORKSPACE, check=True,
                           capture_output=True)
            subprocess.run(["git", "checkout", f"origin/{branch}", "--"] + file_names, cwd=GIT_WORKSPACE, check=True,
                           capture_output=True)
        downloaded_files = [f for f in os.listdir(GIT_WORKSPACE) if os.path.isfile(os.path.join(GIT_WORKSPACE, f))]
        if not downloaded_files:
            st.error("❌ Specified files were not located on target repository branch hierarchy.")
            return False
        st.success(f"✅ Git Sparse-Sync Complete. Synced components: {', '.join(downloaded_files)}")
        return True
    except Exception as e:
        st.error(f"❌ Git tracking synchronization failed: {e}")
        return False


# ------------------------------------------------------------------------------
# UI RENDERING LAYOUT
# ------------------------------------------------------------------------------
st.title("🤖 TigerQE AI Platform - iQEA (Intelligent QE Assistant)")

page_url = st.text_input("Enter the URL of the page:",
                         value=st.session_state.page_url if st.session_state.page_url else "")
st.session_state.page_url = page_url

if st.button("Open Browser"):
    if page_url:
        clean_url = page_url.strip()
        if clean_url and not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--remote-allow-origins=*")
        chrome_options.add_argument("--disable-dev-shm-usage")
        st.session_state.driver = webdriver.Chrome(options=chrome_options)
        st.session_state.driver.get(clean_url)
        st.session_state.driver.maximize_window()
        WebDriverWait(st.session_state.driver, 30).until(utils.is_page_loaded)
        st.success("✅ Browser opened and ready.")
    else:
        st.warning("⚠️ Please enter a URL before opening the browser.")

# ==============================================================================
# ACCORDION 1: USER WORKFLOW RECORDER
# ==============================================================================
if st.session_state.checkbox1_state:
    with st.expander("🔴 User Workflow Recorder"):
        option = st.radio("Choose where to record:", ('Web', 'Desktop'), key="w_recorder_choice")
        if option == 'Web':
            st.subheader("Record User Actions & Capture Screenshots of User Navigation")
            if not st.session_state.recording_started and st.button("🎥 Start Recording"):
                if st.session_state.driver:
                    st.session_state.injected_windows = {}
                    st.session_state.stop_monitor = {"stop": False}
                    st.session_state.actions = []
                    st.session_state.workflow_text = []
                    st.session_state.rb_actions_snapshot = []
                    handle = st.session_state.driver.current_window_handle
                    st.session_state.driver.execute_script(action_utils.injection_script_updated_fixed())
                    st.session_state.injected_windows[handle] = True

                    t1 = threading.Thread(target=utils.thread_new_window_checker,
                                          args=(st.session_state.driver, st.session_state.injected_windows, {},
                                                st.session_state.stop_monitor, page_screenshot_folder,
                                                {"handle": None}), daemon=True)
                    t2 = threading.Thread(target=utils.thread_focus_and_url_monitor,
                                          args=(st.session_state.driver, st.session_state.injected_windows, {},
                                                st.session_state.stop_monitor, page_screenshot_folder,
                                                {"handle": None}), daemon=True)
                    t3 = threading.Thread(target=utils.thread_focus_screenshot,
                                          args=(st.session_state.driver, st.session_state.stop_monitor,
                                                page_screenshot_folder, source), daemon=True)
                    t4 = threading.Thread(target=utils.thread_reinject_action_check,
                                          args=(st.session_state.driver, st.session_state.stop_monitor, {},
                                                {"handle": None}, st.session_state.injected_windows), daemon=True)

                    t1.start()
                    t2.start()
                    t3.start()
                    t4.start()
                    st.session_state.monitor_threads = [t1, t2, t3, t4]
                    st.session_state.recording_started = True
                    st.success("Recording started. Please interact in the browser.")

            if st.session_state.recording_started and st.button("🛑 Stop Recording"):
                st.session_state.actions = action_utils.get_recorded_actions(st.session_state.driver)
                st.session_state.rb_actions_snapshot = list(st.session_state.actions)
                st.session_state.recording_started = False
                st.session_state.stop_monitor["stop"] = True
                st.success("Recording stopped. Performed actions are captured.")

            if st.session_state.actions:
                page_name = st.text_input("Enter Page Name for Saving the Workflow:", key="web_page_name_save")
                if st.button("💾 Save Workflow", key="btn_save_web_wf"):
                    if not page_name:
                        st.warning("⚠ Please enter a name for the workflow.")
                    else:
                        st.session_state.workflow_text = action_utils.generate_workflow_manual(st.session_state.actions)


                        def clean_text(s):
                            return s.replace("\u200b", "").replace("\xa0", " ").strip()


                        cleaned = [clean_text(x) for x in st.session_state.workflow_text]
                        filename = os.path.join(Action_collection, f"{page_name}_actions.txt")
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write("\n".join(cleaned))
                        st.success(f"✅ Workflow saved: {filename}")
                        st.download_button("⬇ Download Workflow", data="\n".join(st.session_state.workflow_text),
                                           file_name=f"{page_name}_actions.txt")
                        st.session_state.actions.clear()

        if option == 'Desktop':
            st.subheader("Record User Actions & Capture Screenshots of User Navigation")
            application_path = st.text_input("Enter full path to application (.exe):",
                                             placeholder=r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE")
            if application_path and not st.session_state.desktop_recording_started:
                if st.button("🎥 Launch and Start Recording"):
                    session = DesktopSession(application_path)
                    session.start(timeout=15)
                    st.session_state.recorder = DesktopRecorder()
                    st.session_state.recorder.start()
                    st.session_state.desktop_recording_started = True
                    st.rerun()
            if st.session_state.desktop_recording_started:
                st.info("🔴 Recording in progress... Interact with the application, then click Stop.")
                if st.button("🛑 Stop Recording"):
                    st.session_state.recorder.stop()
                    st.session_state.desktop_recording_started = False
                    st.rerun()
            if not st.session_state.desktop_recording_started and st.session_state.recorder and st.session_state.recorder.get_actions():
                workflow_name = st.text_input("Enter name for saving the workflow:", key="desk_wf_name")
                if workflow_name and st.button("💾 Save Desktop Workflow"):
                    st.session_state.workflow_text_desktop = st.session_state.recorder.save(workflow_name)
                    st.session_state.recorder = None
                    st.success("✅ Desktop workflow processed successfully.")

        if st.session_state.rb_actions_snapshot:
            with st.expander("⚡ Quick Script Generator (Record & Playback)", expanded=False):
                st.caption(
                    "Generate an automation script directly from your recorded actions — no page file or test case needed.")
                rb_language = st.selectbox("Select target language / framework",
                                           ["Python-Selenium", "Python-Playwright", "Java-Selenium", "Java-Playwright",
                                            "UTAM-JavaScript"], key="rb_language_select")
                rb_script_name = st.text_input("Script file name (without extension):", key="rb_script_name")

                if st.button("⚡ Generate Script from Recording", key="rb_generate_btn"):
                    with st.spinner("Generating script from recorded actions..."):
                        actions_formatted = action_utils.format_actions_for_script_generation(
                            st.session_state.rb_actions_snapshot)
                        script = utils.generate_script_from_recorded_actions(actions_formatted, rb_language)
                        if script:
                            st.session_state.recorded_script = script
                            st.session_state.recorded_script_language = rb_language
                            st.success("✅ Script generated from recording.")
                        else:
                            st.error("Failed to generate script from recording.check the error logs")

                if st.session_state.recorded_script:
                    _rb_lang = st.session_state.recorded_script_language
                    _code_lang = "java" if "java" in _rb_lang.lower() else (
                        "javascript" if "javascript" in _rb_lang.lower() else "python")
                    st.subheader("📝 Generated Script")
                    st.code(st.session_state.recorded_script, language=_code_lang)

                    with st.expander("✏️ Edit before saving", expanded=False):
                        st.text_area("Edit the script:", value=st.session_state.recorded_script, key="rb_script_editor",
                                     height=500)

                    if st.button("💾 Save Script", key="rb_save_btn"):
                        if not rb_script_name:
                            st.warning("Please enter a script file name.")
                        else:
                            final_rb_script = st.session_state.get("rb_script_editor", st.session_state.recorded_script)
                            utils.create_test_file(Test_file_generator, rb_script_name, _rb_lang, final_rb_script)
                            st.success(f"✅ Script saved: {rb_script_name}")

# ==============================================================================
# ACCORDION 2: BDD FEATURE FILE GENERATOR
# ==============================================================================
if st.session_state.checkbox2_state:
    with st.expander("🧾 BDD Feature File Generator"):
        st.title("Feature file Generator using recorded actions")
        Feature_file_name = st.text_input("Enter feature file Name")
        Action_data = ""
        if source == "file":
            Action_data = utils.select_and_read_text_files(Action_collection)
        if st.button("Generate_feature_File"):
            action_prompt = f"Summarize context into valid Cucumber layout structure: {Action_data}"
            feature_response = utils.get_queries_from_ai_updated(action_prompt)
            save_feature_file = os.path.join(feature_file_collection, f"{Feature_file_name}.feature")
            with open(save_feature_file, "w") as file: file.write(feature_response.strip())
            st.write(f"Feature file saved here: {save_feature_file}")

# ==============================================================================
# ACCORDION 3: E2E SCENARIO BASED TEST CASE GENERATOR
# ==============================================================================
if st.session_state.checkbox3_state:
    with st.expander("🧮 E2E Scenario Based Test Case Generator", expanded=True):
        option = st.radio("Choose your Flow with:", ('Documents', 'Recorded_Details'), key="e2e_flow_radio_split")

        if option == 'Recorded_Details':
            st.markdown("**Select Images (Mandatory)**", unsafe_allow_html=True)
            image_files = [f for f in os.listdir(page_screenshot_folder) if
                           f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(
                page_screenshot_folder) else []
            cols = st.columns(5)
            for idx, image_file in enumerate(image_files):
                with cols[idx % 5]:
                    st.image(os.path.join(page_screenshot_folder, image_file), width=100)
                    if image_file not in st.session_state.selected_images:
                        if st.button(f"{image_file}",
                                     key=f"e2e_img_{image_file}"): st.session_state.selected_images.append(image_file)
                    else:
                        if st.button(f"Deselect {image_file}",
                                     key=f"e2e_desel_{image_file}"): st.session_state.selected_images.remove(image_file)
            prompt = st.text_area("Enter the test requirements", "", key="e2e_reqs_input")
            Action_data = utils.select_and_read_text_files(Action_collection) if source == "file" else ""

        elif option == 'Documents':
            source_type = st.selectbox("Select Source Type", options=["Files", "Azure Board", "Jira"],
                                       key="doc_source_type_select")
            uploaded_file = st.file_uploader("Upload requirement definition layout spec document",
                                             type=['pdf', 'docx', 'xlsx', 'txt'])
            Navigation_details = st.text_area("Enter Navigation Details", "", key="doc_nav_details")

        if st.button("Generate Functional Test Cases", key="btn_gen_func_tcs"):
            st.info("Compiling scenario tracking paths matrix directly into project records...")
            # Core analysis mapping calls place here

# ==============================================================================
# ACCORDION 4: PERFORMANCE TEST SCRIPT (JMETER) GENERATOR
# ==============================================================================
if st.session_state.checkbox3_state:
    with st.expander("📊 JMeter Performance Test Script Generator", expanded=True):
        jmx_source_mode = st.radio(
            "Select Script Sourcing Method",
            ["Upload Existing JMX Script File", "Generate with AI via Action File Blueprint"],
            index=1, horizontal=True, key="jmx_source_mode_radio_split"
        )

        if jmx_source_mode == "Upload Existing JMX Script File":
            uploaded_jmx = st.file_uploader("Upload your operational target .jmx file", type=["jmx"],
                                            key="perf_jmx_uploader")
            if uploaded_jmx:
                st.session_state.generated_jmx = uploaded_jmx.getvalue().decode("utf-8")
                st.session_state.generated_jmx_path = os.path.join(JMX_FOLDER, "runtime_api_execution.jmx")
                with open(st.session_state.generated_jmx_path, "w", encoding="utf-8") as f: f.write(
                    st.session_state.generated_jmx)
                st.success("📂 Baseline JMX configuration loaded and cached.")

            # Optional CSV dataset structure block
            st.write("---")
            enable_csv_datasets = st.checkbox("Include Optional Dataset Mapping (.csv)", value=False,
                                              key="enable_csv_datasets_toggle")

            if enable_csv_datasets:
                st.markdown("##### 📊 Map Supporting Execution Datasets (.csv)")
                csv_source_selection = st.radio("Choose CSV Source Strategy", ["Upload CSV Datasets Locally",
                                                                               "Download CSV Datasets from Git Remote Repository"],
                                                key="csv_strategy_perf")
                if csv_source_selection == "Upload CSV Datasets Locally":
                    local_csvs = st.file_uploader("Upload dataset files required by your JMX", type=["csv"],
                                                  accept_multiple_files=True, key="perf_local_csv")
                    if local_csvs:
                        for csv_file in local_csvs:
                            with open(os.path.join(GIT_WORKSPACE, csv_file.name), "wb") as f: f.write(
                                csv_file.getbuffer())
                        st.success("✅ Local data components loaded.")
                else:
                    col_g1, col_g2 = st.columns(2)
                    git_url = col_g1.text_input("Repository Remote URL",
                                                value="https://github.com/SonaJayaram/Performance_IQEAUIIntegration.git",
                                                key="git_url_perf")
                    git_branch = col_g2.text_input("Target Branch / Ref", value="feature/iqea-jmeter-enhancements",
                                                   key="git_branch_perf")
                    col_g3, col_g4 = st.columns(2)
                    git_token = col_g3.text_input("Personal Access Token", type="password", key="git_token_perf")
                    target_csv_files = col_g4.text_input("Comma-Separated Dataset Names to Pull", value="data.csv",
                                                         key="git_csv_perf")
                    if st.button("⚡ Sync Specified Git Data Components", key="btn_sync_git_perf"):
                        file_list = [f.strip() for f in target_csv_files.split(",") if f.strip()]
                        if git_url and file_list:
                            with st.spinner("Downloading datasets via raw endpoints..."):
                                os.makedirs(GIT_WORKSPACE, exist_ok=True)
                                clean_url = git_url.strip().removesuffix(".git").replace("https://github.com/", "")
                                http = urllib3.PoolManager()
                                headers = {"Authorization": f"token {git_token}"} if git_token else {}
                                for remote_file_path in file_list:
                                    raw_url = f"https://raw.githubusercontent.com/{clean_url}/{git_branch}/{remote_file_path}"
                                    resp = http.request('GET', raw_url, headers=headers)
                                    if resp.status == 200:
                                        local_target_filename = os.path.basename(remote_file_path)
                                        with open(os.path.join(GIT_WORKSPACE, local_target_filename), "wb") as f:
                                            f.write(resp.data)
                                        st.success(f"✅ Downloaded and cached: {local_target_filename}")
                                    else:
                                        st.error(
                                            f"❌ Download failed for path: {remote_file_path} (Status: {resp.status})")

        elif jmx_source_mode == "Generate with AI via Action File Blueprint":
            action_folder = Action_collection
            action_files = [f for f in os.listdir(action_folder) if f.endswith("_actions.txt")] if os.path.exists(
                action_folder) else []
            if not action_files:
                st.warning("⚠ No recorded workflow action logs found in workspace.")
            else:
                selected_action_file = st.selectbox("Select Recorded Workflow Profile", options=action_files,
                                                    key="sb_perf_action_file")
                with open(os.path.join(action_folder, selected_action_file), "r", encoding="utf-8") as f:
                    actions_lines = f.read()
                ai_prompt = st.text_area("Enter Additional Performance Test Settings",
                                         value="Generate Jmeter compatible jmx script with 10 users, 5 seconds rampup, 10 loops and 120 seconds test duration",
                                         key="ta_perf_ai_settings")

                if st.button("🚀 Generate AI-based JMX", key="btn_perf_gen_jmx"):
                    user_prompt = f"Generate complete valid executable JMeter 5.5 structure for following workflows:\n{actions_lines}\n\nAdditional parameters:\n{ai_prompt}"
                    with st.spinner("Calling Core LLM Orchestrator via proxy paths..."):
                        raw_ai = utilitymodule.get_output_from_ai(user_prompt)
                        if raw_ai is None:
                            st.error("❌ JMX generation failed.")
                        else:
                            ai_config = utilitymodule.extract_ai_test_config(ai_prompt, raw_ai)
                            st.session_state.generated_jmx = utilitymodule.update_jmx_file(raw_ai.strip(), ai_config)
                            st.session_state.generated_jmx_path = os.path.join(JMX_FOLDER,
                                                                               f"{selected_action_file.replace('_actions.txt', '')}.jmx")
                            with open(st.session_state.generated_jmx_path, "w", encoding="utf-8") as f:
                                f.write(st.session_state.generated_jmx)
                            st.success("✅ JMX generated successfully!")

        # 🎛️ COCKPIT CONTROLLER REMAINS INTEGRATED UNDER GENERATOR PER USER REQUIREMENT
        if st.session_state.generated_jmx:
            st.write("---")
            st.markdown("#### ⚙️ JMX Performance Execution Setup")
            execution_profile = st.selectbox("Choose Environment Infrastructure Config",
                                             ["Local Dry Run / Smoke Test (Your Machine Only)",
                                              "Actual Load Test (Distributed Master-Slave Config)"],
                                             key="exec_env_matrix_split")

            st.markdown("##### ⚙️ Overriding Target Execution Runtime Properties")
            col_u1, col_u2, col_u3, col_u4 = st.columns(4)

            if "Local Dry Run" in execution_profile:
                target_num_threads = col_u1.number_input("Concurrent Users (Threads)", min_value=1, value=1, step=1,
                                                         key="num_threads_input")
                target_ramp_time = col_u2.number_input("Ramp-Up Period (Seconds)", min_value=1, value=1, step=1,
                                                       key="ramp_time_input")
                target_loop_count = col_u3.number_input("Loop Interactions (-1 for Infinite)", min_value=-1, value=1,
                                                        step=1, key="loop_count_input")
                target_duration_time = col_u4.number_input("Test Run Schedule (Seconds)", min_value=0, value=5, step=1,
                                                           key="duration_input")
                master_ip_value = "localhost"
            else:
                target_num_threads = col_u1.number_input("Concurrent Users (Threads)", min_value=1, value=10, step=1,
                                                         key="num_threads_input")
                target_ramp_time = col_u2.number_input("Ramp-Up Period (Seconds)", min_value=1, value=5, step=1,
                                                       key="ramp_time_input")
                target_loop_count = col_u3.number_input("Loop Interactions (-1 for Infinite)", min_value=-1, value=-1,
                                                        step=1, key="loop_count_input")
                target_duration_time = col_u4.number_input("Test Run Schedule (Seconds)", min_value=1, value=120,
                                                           step=1, key="duration_input")

            st.write("---")
            st.markdown("### 📊 Live Telemetry Metric Redirection")
            grafana_url = st.text_input("Your Grafana Dashboard URL",
                                        value="http://localhost:3000/d/adf2bsx/iqeadashboard?orgId=1&refresh=5s&panelId=1",
                                        key="grafana_url_input_split")
            if "http" in grafana_url:
                st.markdown(
                    f'<a href="{grafana_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#800080;color:white;text-align:center;padding:10px;border-radius:5px;font-weight:bold;font-size:16px;margin-bottom:15px;cursor:pointer;">📈 Open Live Grafana Monitor Dashboard</div></a>',
                    unsafe_allow_html=True)

            if "Actual Load Test" in execution_profile:
                local_master_ip = st.text_input("Master VM Infrastructure IP", value="10.0.0.4",
                                                key="runtime_master_ip_input_split")
                remote_slave_ip = st.text_input("Slave VM Target Node IP", value="10.0.0.5", disabled=True)
                master_ip_value = local_master_ip if local_master_ip else "10.0.0.4"

            if st.button("🚀 Fire Performance Execution Plan", key="btn_fire_performance_plan_split_main"):
                st.info("Initiating orchestration pipeline and running target test context configuration...")
                jmx_full_path = st.session_state.generated_jmx_path

                if not jmx_full_path or not os.path.exists(jmx_full_path):
                    st.error("❌ Execution target configuration missing.")
                else:
                    jmeter_path = r"F:\Sona_Performance\apache-jmeter-5.6.3\apache-jmeter-5.6.3\bin\jmeter.bat"

                    with open(jmx_full_path, "r", encoding="utf-8") as f:
                        original_jmx = f.read()
                    base_name = os.path.basename(jmx_full_path).replace(".jmx", "")
                    ai_config = {"threads": int(target_num_threads), "rampup": int(target_ramp_time),
                                 "loops": int(target_loop_count), "duration": int(target_duration_time)}

                    updated_jmx = utilitymodule.update_jmx_file(original_jmx, ai_config)
                    updated_jmx = utilitymodule.patch_influx_endpoint(updated_jmx, master_ip_value)

                    try:
                        root_xml = ET.fromstring(updated_jmx)
                        for element in root_xml.iter("CSVDataSet"):
                            for prop in element.iter("stringProp"):
                                if prop.attrib.get("name") == "filename":
                                    prop.text = os.path.basename(prop.text)
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

                    jmeter_bin_directory = os.path.dirname(jmeter_path)
                    custom_env = os.environ.copy()
                    if jmeter_bin_directory: custom_env["JMETER_HOME"] = os.path.dirname(jmeter_bin_directory)
                    custom_env[
                        "JVM_ARGS"] = f"-Djava.rmi.server.hostname={master_ip_value} -Dclient.rmi.localport=60000 -Dserver.rmi.ssl.disable=true"

                    try:
                        process = subprocess.Popen(command, shell=True, env=custom_env, cwd=current_path,
                                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        log_stdout_box = st.empty()
                        accumulated_logs = ""
                        max_allowed_seconds = int(target_duration_time) + 60
                        start_time = datetime.now()

                        while True:
                            line = process.stdout.readline()
                            if line:
                                accumulated_logs += line
                                log_stdout_box.code(accumulated_logs[-3000:])
                            if not line and process.poll() is not None: break
                            if (datetime.now() - start_time).total_seconds() > max_allowed_seconds:
                                st.warning("⚠️ Workload timeframe window hit.")
                                break

                        if process.poll() is None:
                            subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True, stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL)
                        process.wait()
                        time.sleep(3)

                        if os.path.exists(output_jtl) and os.path.getsize(output_jtl) > 100:
                            if os.path.exists(html_report_dir): shutil.rmtree(html_report_dir, ignore_errors=True)
                            st.info("📊 Generating JMeter HTML Dashboard Assets...")
                            report_process = subprocess.run([jmeter_path, "-g", output_jtl, "-o", html_report_dir],
                                                            shell=True, cwd=jmeter_bin_directory, env=custom_env,
                                                            capture_output=True, text=True)
                            if report_process.returncode == 0:
                                st.success("✅ HTML Report generated successfully.")
                            else:
                                st.error("❌ HTML Report compilation sequence encountered warnings.")
                        else:
                            st.error("❌ Log data was empty.")
                    except Exception as ex:
                        st.error(f"❌ Core engine configuration crash: {ex}")

        if st.session_state.generated_jmx:
            st.write("---")
            st.subheader("📄 Generated JMX Blueprint Output")
            st.code(st.session_state.generated_jmx, language="xml")
            target_download_filename = os.path.basename(
                st.session_state.generated_jmx_path) if st.session_state.generated_jmx_path else "api_performance_plan.jmx"
            st.download_button(label="⬇ Download Plan Layout", data=st.session_state.generated_jmx,
                               file_name=target_download_filename, mime="application/xml")

# ==============================================================================
# ACCORDION 5: ACTION-DRIVEN TEST DATA GENERATOR
# ==============================================================================
if st.session_state.checkbox4_state:
    with st.expander("🧪 Action-Driven Test Data Generator"):
        st.title("Enhanced Test Data Generator (Based on Action File)")
        st.session_state.test_data_action_data = ""
        st.session_state.test_files_content = ""
        if source == "file":
            st.session_state.test_files_content = utils.select_and_read_text_files_xpath(
                "test data generation -Test Cases files", Test_case_collection)
            st.session_state.test_data_action_data = utils.select_and_read_text_files_xpath(
                "test data generation -Recorded actions files", Action_collection)

        st.markdown("**Enter the additional information or sample data** <span style='color:red;'>*</span>",
                    unsafe_allow_html=True)
        st.session_state.test_data_addition_info = st.text_area("Optional: Provide additional test data", "",
                                                                key="user_data_textarea")
        if st.button("Generate Functional Test Data"):
            if st.session_state.test_data_action_data:
                constructed_prompt = utils.generate_promot_test_data_generator("test_data",
                                                                               st.session_state.test_data_action_data,
                                                                               st.session_state.test_files_content,
                                                                               st.session_state.test_data_addition_info)
                st.session_state.test_data_llm_response = utils.get_queries_from_ai_updated(constructed_prompt)
                st.success("Test data matrix generated cleanly.")
            else:
                st.error("Please select action file")
        if st.session_state.test_data_llm_response:
            test_data_file_name = st.text_input("Enter the testdata file Name:")
            if st.button("Save Test Data"):
                if test_data_file_name:
                    utils.save_test_data_into_excel(st.session_state.test_data_llm_response, test_data_file_name,
                                                    test_data_folder)
                    st.success("Test data generated successfully")
                else:
                    st.error("Please select test data file name")

# ==============================================================================
# ACCORDION 6: LOCATORS POM FILE GENERATOR
# ==============================================================================
if st.session_state.checkbox5_state:
    with st.expander("🔎 Locators 🧾 POM File Generator", expanded=st.session_state.open_expander_collection):
        st.title("Locator Generator for Visible Elements")

        selected_app = st.multiselect("Select application type:", ["PowerBi", "Web"], default=["Web"])
        tags_placeholder = st.empty()
        if "Web" in selected_app:
            selected_tags = tags_placeholder.multiselect("Select element types to extract:", xpath_tag_keys,
                                                         default=st.session_state.selected_tags,
                                                         key="selected_tags_multiselect")
        else:
            tags_placeholder.empty()
            selected_tags = []

        st.session_state.selected_app = selected_app
        st.markdown("<a name='top-button'></a>", unsafe_allow_html=True)
        collect_clicked = st.button("Collecting Elements", key="collect_btn")

        if collect_clicked:
            st.session_state.selected_tags = selected_tags
            handles = st.session_state.driver.window_handles
            if len(handles) > 1:
                st.session_state.driver.switch_to.window(handles[-1])

            for key in ["prompt_response", "selected_xpaths", "prompt_response_page_file", "show_popup", "show_form"]:
                if key in st.session_state:
                    st.session_state[key] = "" if "response" in key else False

            st.session_state.selected_xpaths = []
            st.session_state.prompt_response = ""
            page_identifier = st.session_state.driver.current_url
            if "PowerBi" in selected_app:
                formatted_summary = utils.get_visible_element_powerBi(st.session_state.driver, page_identifier)
            if "Web" in selected_app:
                formatted_summary = utils.get_visible_element_iframe(st.session_state.driver, page_identifier,
                                                                     st.session_state.selected_tags)
            if formatted_summary is None:
                formatted_summary = []
            if formatted_summary:
                if "PowerBi" in selected_app:
                    st.session_state.prompt_response = utils.get_queries_from_ai("PowerBi", formatted_summary)
                if "Web" in selected_app:
                    st.session_state.prompt_response = utils.get_queries_from_ai("Web", formatted_summary)
            else:
                st.info("No elements found in selected tag")

        if st.session_state.prompt_response:
            xpath_dict = utils.filter_duplicate_xpaths(utils.selecting_xpath(st.session_state.prompt_response))
            st.title("Select XPath Expressions to Add to Excel")
            xpath_output_placeholder = st.empty()
            with xpath_output_placeholder.container():
                st.session_state.selected_xpaths = utils.adding_xpath_user_view(xpath_dict)
            page_name = st.text_input("Enter the Page Name:")
            if st.button("Add Selected XPaths to Excel"):
                if page_name and st.session_state.selected_xpaths:
                    utils.adding_selected_xapth_excel(page_name)
                    st.session_state.show_popup = True
                    st.session_state.show_form = False
                elif not st.session_state.selected_xpaths:
                    st.error("Select at-least one xpath to add")
                elif not page_name:
                    st.error("Enter the Page name to add the selected xpath")

            if st.session_state.show_popup and not st.session_state.show_form:
                st.write("**Do you want to generate the page file?**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes"):
                        st.session_state.show_popup = False
                        st.session_state.show_form = True
                with col2:
                    if st.button("No"):
                        st.session_state.show_popup = False
                        st.session_state.show_form = False
                        st.session_state.prompt_response = ""
                        st.session_state.xpath_for_new_page_user_info = True
                        st.rerun()

            if st.session_state.show_form:
                st.header("Generating Page File")
                page_name = st.text_input("Enter Page Name (same as xpath details)", value=page_name)
                language = st.selectbox("Select Language",
                                        ["Java-Selenium", "Java-Playwright", "Python-Selenium", "Python-Playwright"])
                Action_data = ""
                if source == "file":
                    Action_data = utils.select_and_read_text_files_xpath("xpath", Action_collection)

                if st.button("Generate Page File"):
                    st.session_state.prompt_response_page_file = ""
                    Prompt = utils.generate_pom_from_excel_with_action(language, page_name, language, Action_data)
                    st.session_state.prompt_response_page_file = utils.get_queries_from_ai("Page_File", Prompt)
                    st.subheader("Generated Page Class")
                    if source == "file":
                        utils.create_java_file(page_name, language, st.session_state.prompt_response_page_file)
                        st.success(f"Page file generated for '{page_name}' in '{language}' language.")
                        st.session_state.xpath_for_new_page = True

        if st.session_state.xpath_for_new_page and st.button("Continue for New Page"):
            st.session_state.prompt_response_page_file = ""
            st.session_state.prompt_response = ""
            st.session_state.selected_xpaths = []
            st.session_state.show_popup = False
            st.session_state.show_form = False
            st.session_state.xpath_for_new_page = False
            st.session_state.xpath_for_new_page_user_info = True
            st.rerun()

        if st.session_state.xpath_for_new_page_user_info:
            st.info("Please change to the new page in the browser and click 'Collecting Elements' again.")
            st.session_state.xpath_for_new_page_user_info = False

# ==============================================================================
# ACCORDION 6: TEST AUTOMATION SCRIPT GENERATOR
# ==============================================================================
if st.session_state.checkbox6_state:
    st.session_state.failed_files = []
    with st.expander("🧾 Test Automation Script Generator"):
        st.title("Automation Script Generator using page file and test cases")
        test_file_name = st.text_input("Enter the test File Name")
        test_file_language = st.selectbox("Select Language for test file",
                                          ["Java-Selenium", "Java-Playwright", "Python-Selenium", "Python-Playwright",
                                           "Desktop & Web[python-Selenium]", "UTAM-JavaScript"])
        if test_file_language != "Desktop & Web[python-Selenium]":
            page_files_content = ""
            test_files_content = ""
            Action_data = ""
            if source == "file":
                page_files_content = utils.select_and_read_text_files_xpath("page_test", Page_collection)
                test_files_content = utils.select_and_read_text_files_xpath("testcase_test", Test_case_collection)
                Action_data = utils.select_and_read_text_files_xpath("recorded action (Optional)", Action_collection)

            if st.button("Generate_Test_Script", key="gen_script_main"):
                Lang_lib = "Test-" + test_file_language
                Prompt = utils.generate_test_script(Lang_lib, test_file_language, page_files_content,
                                                    test_files_content, Action_data)
                test_script_response = utils.get_queries_from_ai_updated(Prompt)
                st.session_state.generated_test_script = test_script_response
                st.session_state.script_gen_inputs = {
                    "test_file_language": test_file_language,
                    "page_files_content": page_files_content,
                    "test_files_content": test_files_content,
                    "Action_data": Action_data,
                    "source": source,
                    "flow": "standard"
                }
                st.session_state.script_editor_version = st.session_state.get("script_editor_version", 0) + 1
                st.rerun()
        else:
            test_windows_application_path = st.text_input("Enter the test_windows_application_path ")
            Action_data = ""
            if source == "file":
                Action_data = utils.select_and_read_text_files_xpath("recorded action", Action_collection)
            if st.button("Generate_Test_Script", key="gen_script_desktop"):
                Lang_lib = "Test-" + test_file_language
                Prompt = utils.generate_test_script_windows_web(Lang_lib, Action_data, test_windows_application_path)
                test_script_response = utils.get_queries_from_ai_updated(Prompt)
                st.session_state.generated_test_script = test_script_response
                st.session_state.script_gen_inputs = {
                    "test_file_language": test_file_language,
                    "page_files_content": "",
                    "test_files_content": "",
                    "Action_data": Action_data,
                    "source": source,
                    "flow": "desktop"
                }
                st.session_state.script_editor_version = st.session_state.get("script_editor_version", 0) + 1
                st.rerun()
        if st.session_state.get("generated_test_script"):
            ver = st.session_state.get("script_editor_version", 0)
            _lang = st.session_state.script_gen_inputs.get("test_file_language", "")
            _code_lang = "java" if "java" in _lang.lower() else (
                "javascript" if "javascript" in _lang.lower() else "python")

            st.subheader("📝 Generated Script")
            st.code(st.session_state.generated_test_script, language=_code_lang)

            with st.expander("✏️ Edit Script (expand to modify before saving)"):
                edited_script = st.text_area("Edit the script here:", value=st.session_state.generated_test_script,
                                             key=f"script_editor_{ver}", height=500)

            st.subheader("💬 Review Feedback")
            review_details = st.text_area("Enter specific review details, issues, or requirements (optional):",
                                          value="", key=f"script_review_{ver}", height=150,
                                          placeholder="e.g., 'TC02 step 3 is missing'...")
            col_save, col_regen = st.columns(2)
            with col_save:
                if st.button("💾 Save Generated Script", key="save_script_btn"):
                    final_script = st.session_state.get(f"script_editor_{ver}", st.session_state.generated_test_script)
                    gen_source = st.session_state.script_gen_inputs.get("source", source)
                    if gen_source == "file":
                        utils.create_test_file(Test_file_generator, test_file_name, test_file_language, final_script)
                    st.success("✅ Script saved successfully!")
                    st.session_state.generated_test_script = None
            with col_regen:
                if st.button("🔄 Regenerate Script", key="regen_script_btn"):
                    current_script = st.session_state.get(f"script_editor_{ver}",
                                                          st.session_state.generated_test_script)
                    current_review = st.session_state.get(f"script_review_{ver}", "")
                    inputs = st.session_state.script_gen_inputs
                    regen_prompt = utils.generate_code_review_prompt(inputs["test_file_language"],
                                                                     inputs.get("page_files_content", ""),
                                                                     inputs.get("test_files_content", ""),
                                                                     inputs.get("Action_data", ""), current_script,
                                                                     current_review)
                    regenerated_script = utils.get_queries_from_ai_updated(regen_prompt)
                    st.session_state.generated_test_script = regenerated_script
                    st.session_state.script_editor_version = ver + 1
                    st.rerun()

# ==============================================================================
# ACCORDION 7: SOURCE CODE AUTOMATION BRIDGE
# ==============================================================================
if st.session_state.checkbox7_state:
    with st.expander("⚙️ Source Code 📡 Automation Bridge"):
        st.title("Upload code to Repository")
        if source == "file":
            pytest_files = utils.select_and_read_text_files_xpath("test_file", utils.Test_file_generator)
            pom_files = utils.select_and_read_text_files_xpath("pom_file", utils.Page_file_generator)
        repo_pom_name = st.text_input("Enter folder name in repo:", value="test_web/src/pom/pages",
                                      key="bridge_pom_folder")
        repo_pytest_name = st.text_input("Enter folder name in repo:", value="test_web/tests/test_cases",
                                         key="bridge_pytest_folder")

        if st.button("Push to Repo"):
            token = os.getenv("GITLAB_ACCESS_TOKEN")
            if token:
                try:
                    g = Gitlab("https://git.tigeranalytics.com/", private_token=token, ssl_verify=False)
                    g.auth()
                    print("✅ Authentication successful!")
                except Exception as e:
                    print("❌ Auth failed:", e)
            repo = g.projects.get(os.getenv("GITLAB_REPO_NAME"))
            branch = os.getenv("GITLAB_BRANCH_NAME", "main")

            if repo_pom_name and repo_pytest_name:
                if source == "file":
                    for file_name, content in pom_files.items():
                        pom_dest_path = f"{repo_pom_name.strip('/')}/{file_name}"
                        utils.push_file_to_gitlab(pom_dest_path, content, repo, branch)
                    for file_name, content in pytest_files.items():
                        pytest_dest_path = f"{repo_pytest_name.strip('/')}/{file_name}"
                        utils.push_file_to_gitlab(pytest_dest_path, content, repo, branch)

# ==============================================================================
# ACCORDION 8: DOWNLOAD ARTIFACTS
# ==============================================================================
if st.session_state.checkbox8_state:
    if source == "database":
        with st.expander("📥 Download Artifacts"):
            st.title("Download Artifacts from Database")
            file_type = st.selectbox("Select FileType",
                                     ["Recorded_Action_file", "Page_file", "Test_file", "Testcase_file"])
            selected_files = []

            if st.button("📦 Download Files"):
                st.warning("⚠️ Sourcing configuration set to local filesystem workspace mode.")

# ==============================================================================
# ACCORDION 9: ACTIVE AUTOMATION TEST EXECUTION & ALLURE REPORTING
# ==============================================================================
if st.session_state.checkbox9_state:
    with st.expander("🚀 Test Execution & Allure Reporting", expanded=True):
        st.title("Execute Generated Test Scripts and View Allure Reports")

        if source == "file":
            test_files = [f for f in os.listdir(Test_file_generator) if f.endswith('.py')]
            selected_file = st.selectbox("Select Test Script to Execute", test_files,
                                         key="test_file_select") if test_files else None

        if selected_file:
            # 💡 RESTORED NATIVE PYTEST TRIGGER BLOCK
            if st.button("Run Test Script"):
                if source == "file":
                    test_path = os.path.join(Test_file_generator, selected_file)
                if test_path:
                    command = f"python -m pytest -q --alluredir=allure-results {test_path}"
                    try:
                        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=current_path)
                        st.session_state.test_execution_status = result.stdout + "\n" + result.stderr
                        if result.returncode == 0:
                            st.success("✅ Test execution completed successfully.")
                        else:
                            st.warning("⚠️ Test execution completed with issues.")
                        st.text_area("Execution Output", st.session_state.test_execution_status, height=200)
                    except Exception as e:
                        st.error(f"❌ Error running test: {e}")

            # 💡 RESTORED NATIVE ALLURE REPORT GENERATOR
            if st.button("View Allure Report"):
                command = "allure serve allure-results"
                try:
                    subprocess.Popen(command, shell=True, cwd=current_path)
                    st.success("✅ Allure report server started. The report should open automatically in your browser.")
                except Exception as e:
                    st.error(f"❌ Error starting Allure server: {e}")
        else:
            st.info("ℹ️ No test scripts available.")

# Footer of webpage
st.divider()
st.markdown("### Contact Us\n- Reach us at [QE Core Team](mailto:sahil.gupta@tigeranalytics.com)")

# Checkbox mapping control structure
col0, col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(10)
with col0: st.write("Choose display")
with col1:
    checkbox1 = st.checkbox("(1)", value=st.session_state.checkbox1_state, key="cb1")
    if st.session_state.checkbox1_state != checkbox1: st.session_state.checkbox1_state = checkbox1; st.rerun()
with col2:
    checkbox2 = st.checkbox("(2)", value=st.session_state.checkbox2_state, key="cb2")
    if st.session_state.checkbox2_state != checkbox2: st.session_state.checkbox2_state = checkbox2; st.rerun()
with col3:
    checkbox3 = st.checkbox("(3)", value=st.session_state.checkbox3_state, key="cb3")
    if st.session_state.checkbox3_state != checkbox3: st.session_state.checkbox3_state = cb3; st.rerun()
with col4:
    checkbox4 = st.checkbox("(4)", value=st.session_state.checkbox4_state, key="cb4")
    if st.session_state.checkbox4_state != checkbox4: st.session_state.checkbox4_state = checkbox4; st.rerun()
with col5:
    checkbox5 = st.checkbox("(5)", value=st.session_state.checkbox5_state, key="cb5")
    if st.session_state.checkbox5_state != checkbox5: st.session_state.checkbox5_state = checkbox5; st.rerun()
with col6:
    checkbox6 = st.checkbox("(6)", value=st.session_state.checkbox6_state, key="cb6")
    if st.session_state.checkbox6_state != checkbox6: st.session_state.checkbox6_state = checkbox6; st.rerun()
with col7:
    checkbox7 = st.checkbox("(7)", value=st.session_state.checkbox7_state, key="cb7")
    if st.session_state.checkbox7_state != checkbox7: st.session_state.checkbox7_state = checkbox7; st.rerun()
with col8:
    checkbox8 = st.checkbox("(8)", value=st.session_state.checkbox8_state, key="cb8")
    if st.session_state.checkbox8_state != checkbox8: st.session_state.checkbox8_state = checkbox8; st.rerun()
with col9:
    checkbox9 = st.checkbox("(9)", value=st.session_state.checkbox9_state, key="cb9")
    if st.session_state.checkbox9_state != checkbox9: st.session_state.checkbox9_state = checkbox9; st.rerun()