import subprocess
from github import Github, GithubException  # Make sure GithubException is imported
from gitlab import Gitlab
import pandas as pd
import re
from github import Github
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
import utilities.Utilities_Xpath as utils
import utilities.utils_action as action_utils
import utilities.db_utils.handler as db_handler
import utilities.TMT_Connection.Test_management_tool_utils as tmt_utils
from PIL import Image
import pytesseract
import io
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv; load_dotenv()
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#setting details - source either file or database
from config.settings_reader import get_source, get_update_user,get_model,get_xpath_key
from desktop.session import *
from desktop.recorder import *
source = get_source()
model_type= get_model()
xpath_tag_keys= get_xpath_key()

# Setup output folder
current_path = os.getcwd()
input_folder = os.path.join(current_path, "Input")
output_folder = os.path.join(current_path, "output")
Action_collection = os.path.join(output_folder, "Action_collection")
Action_collection_desktop=os.path.join(Action_collection, "Action_collection_desktop")
Page_collection = os.path.join(output_folder, "page_file_generator")
Test_case_collection = os.path.join(output_folder, "Test_Cases_collection")
Test_file_generator = os.path.join(output_folder, "test_file_generator")
feature_file_collection = os.path.join(output_folder, "Feature_file_generator")
test_data_folder=os.path.join(output_folder, "Test_data_generator")
api_template_file=os.path.join(input_folder,"Api_template.xlsx")
os.makedirs(Page_collection, exist_ok=True)
os.makedirs(Test_case_collection, exist_ok=True)
os.makedirs(Action_collection, exist_ok=True)
os.makedirs(feature_file_collection, exist_ok=True)
os.makedirs(test_data_folder, exist_ok=True)
os.makedirs(Action_collection_desktop,exist_ok=True)
#page_screenshot_folder_new = os.path.join(Action_collection, "page_screenshot_valid")
page_screenshot_folder = os.path.join(Action_collection, "Sauce_demo")
os.makedirs(page_screenshot_folder, exist_ok=True)
os.makedirs(Test_file_generator, exist_ok=True)

st.set_page_config(
    page_title="TigerQE AI iQEA",
    page_icon="🤖",
    layout="centered"
)

# Session state setup
if "page_url" not in st.session_state:
    st.session_state.page_url=None
if "repo_url" not in st.session_state:
    st.session_state.repo_url=None
if "selected_images" not in st.session_state:
    st.session_state.selected_images = []
if "show_popup" not in st.session_state:
    st.session_state.show_popup = False
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if 'stop_monitor' not in st.session_state:
    st.session_state.stop_monitor = {"stop": False}
if 'monitor_thread' not in st.session_state:
    st.session_state.monitor_thread = None
if 'driver' not in st.session_state:
    st.session_state.driver = None
if 'recording_started' not in st.session_state:
    st.session_state.recording_started = False
if 'actions' not in st.session_state:
    st.session_state.actions = []
if 'selected_xpaths' not in st.session_state:
    st.session_state.selected_xpaths = []
if 'prompt_response' not in st.session_state:
    st.session_state.prompt_response = ""
if 'prompt_response_page_file' not in st.session_state:
    st.session_state.prompt_response_page_file=""
if 'last_page' not in st.session_state:
    st.session_state.last_page = None
if 'selected_tags' not in st.session_state:
        st.session_state.selected_tags = ["input", "button"]
if 'selected_app' not in st.session_state:
    st.session_state.selected_app = []
if 'requirements_details' not in st.session_state:
    st.session_state.requirements_details = None
if 'accuracy_response' not in st.session_state:
    st.session_state.accuracy_response = None
if 'testcase_response' not in st.session_state:
    st.session_state.testcase_response = []
if 'scenario_response' not in st.session_state:
    st.session_state.scenario_response = []
if 'all_testcases' not in st.session_state:
    st.session_state.all_testcases = []
if 'testcase_regeneration' not in st.session_state:
    st.session_state.testcase_regeneration = None
# if 'st.session_state.all_responses' not in st.session_state:
#     st.session_state.all_responses = []
if 'overall_accuracy' not in st.session_state:
    st.session_state.overall_accuracy = None
# Unique key for session state
if "scroll_to_top" not in st.session_state:
    st.session_state.scroll_to_top = False
if "checkbox1_state" not in st.session_state:
    st.session_state.checkbox1_state = True
if "checkbox2_state" not in st.session_state:
    st.session_state.checkbox2_state = False
if "checkbox3_state" not in st.session_state:
    st.session_state.checkbox3_state = True
if "checkbox4_state" not in st.session_state:
    st.session_state.checkbox4_state = True
if "checkbox5_state" not in st.session_state:
    st.session_state.checkbox5_state = True
if "checkbox6_state" not in st.session_state:
    st.session_state.checkbox6_state = True
if "checkbox7_state" not in st.session_state:
    st.session_state.checkbox7_state = True
if "checkbox8_state" not in st.session_state:
    st.session_state.checkbox8_state = True
if "checkbox9_state" not in st.session_state:
    st.session_state.checkbox9_state = True
if "failed_files" not in st.session_state:
    st.session_state.failed_files = []
if "regenerate_clicked" not in st.session_state:
    st.session_state.regenerate_clicked = False
if "save_testcases" not in st.session_state:
    st.session_state.save_testcases = False
if "save_regenerated_testcases" not in st.session_state:
    st.session_state.save_regenerated_testcases = False
if 'workflow_text' not in st.session_state:
    st.session_state.workflow_text = []
if "generated_test_script" not in st.session_state:
    st.session_state.generated_test_script = None
if "script_gen_inputs" not in st.session_state:
    st.session_state.script_gen_inputs = {}
if "script_editor_version" not in st.session_state:
    st.session_state.script_editor_version = 0
if 'injected_windows' not in st.session_state:
    st.session_state.injected_windows= {}
if 'workflow_text_desktop' not in st.session_state:
    st.session_state.workflow_text_desktop = []
if "xpath_for_new_page" not in st.session_state:
    st.session_state.xpath_for_new_page = False
if "xpath_for_new_page_user_info" not in st.session_state:
    st.session_state.xpath_for_new_page_user_info = False

# ── Record & Playback session state ──
if "recorded_script" not in st.session_state:
    st.session_state.recorded_script = None
if "recorded_script_language" not in st.session_state:
    st.session_state.recorded_script_language = "Python-Selenium"
if "rb_actions_snapshot" not in st.session_state:
    st.session_state.rb_actions_snapshot = []

# --- Track expander state only for collection ---
if "open_expander_collection" not in st.session_state:
    st.session_state.open_expander_collection = False
if "recorded_actions_history" not in st.session_state:
    st.session_state.recorded_actions_history = False

# ---------- TMT integration----------
# ── Test Management Tool (TMT) gap analysis session state ──
if "tmt_tool" not in st.session_state:
    st.session_state.tmt_tool = "None"
if "tmt_connected" not in st.session_state:
    st.session_state.tmt_connected = False
if "tmt_existing_tcs" not in st.session_state:
    st.session_state.tmt_existing_tcs = []
if "tmt_selected_plan_id" not in st.session_state:
    st.session_state.tmt_selected_plan_id = None
if "tmt_selected_suite_id" not in st.session_state:
    st.session_state.tmt_selected_suite_id = None
if "tmt_plans" not in st.session_state:
    st.session_state.tmt_plans = []
if "tmt_suites" not in st.session_state:
    st.session_state.tmt_suites = []
if "gap_analysis_result" not in st.session_state:
    st.session_state.gap_analysis_result = None
if "tmt_jira_project_key" not in st.session_state:
    st.session_state.tmt_jira_project_key = ""
if "tmt_fetch_type" not in st.session_state:
    st.session_state.tmt_fetch_type = "Test Cases"
if "tmt_gap_approved" not in st.session_state:
    st.session_state.tmt_gap_approved = False
if "tmt_replacement_responses" not in st.session_state:
    st.session_state.tmt_replacement_responses = []
if "tmt_deletion_notice" not in st.session_state:
    st.session_state.tmt_deletion_notice = []
if "tmt_gen_inputs" not in st.session_state:
    st.session_state.tmt_gen_inputs = {}

if "document_source_selector" not in st.session_state:
    st.session_state.document_source_selector = "Files"   # default

if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None

if "azure_workitem_id" not in st.session_state:
    st.session_state.azure_workitem_id = ""

if "jira_workitem_id" not in st.session_state:
    st.session_state.jira_workitem_id = ""
if "excel_path" not in st.session_state:
    st.session_state.excel_path = ""
### test_data_generate
if "test_data_action_data" not in st.session_state:
    st.session_state.test_data_action_data = ""
if "test_files_content" not in st.session_state:
    st.session_state.test_files_content = ""
if "test_data_addition_info" not in st.session_state:
    st.session_state.test_data_addition_info= ""
if "test_data_llm_response" not in st.session_state:
    st.session_state.test_data_llm_response= ""
#### Api
if "api_data" not in st.session_state:
    st.session_state.api_data= ""
####xpath
if "select_all" not in st.session_state:
    st.session_state.select_all = False

st.title(" 🤖 TigerQE AI Platform - iQEA (Intelligent QE Assistant)")

###desktop
if "desktop_action_name" not in st.session_state:
    st.session_state.desktop_action_name = ""
if "recorder" not in st.session_state:
    st.session_state.recorder = DesktopRecorder()

##playback
if "rb_language" not in st.session_state:
    st.session_state.rb_language = "Python-Selenium"
# 1. Open the browser
page_url = st.text_input("Enter the URL of the page:")
st.session_state.page_url = page_url
if st.button("Open Browser"):
    if page_url:
        clean_url = page_url.strip()
        if clean_url and not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url
        if not clean_url:
            st.warning("⚠️ Please enter a valid URL.")
        else:
            chromedriver_path = os.path.join(input_folder, "chromedriver.exe")
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

# Display sections based on checkboxes
if st.session_state.checkbox1_state:
    with (st.expander("🔴 User Workflow Recorder")):
        option = st.radio(
            "Choose where to record:",
            ('Web', 'Desktop')
        )
        if option == 'Web':
            # 2. Start Recording
            st.subheader("Record User Actions & Capture Screenshots of User Navigation")
            st.session_state.workflow_text = []
            if not st.session_state.recording_started and st.button("🎥 Start Recording"):
                if st.session_state.driver:
                    # --- Stop any existing monitor threads ---
                    if "monitor_threads" in st.session_state:
                        st.session_state.stop_monitor["stop"] = True
                        for t in st.session_state.monitor_threads:
                            if t and t.is_alive():
                                t.join(timeout=2)

                    # --- Reset recording state ---
                    st.session_state.injected_windows = {}
                    st.session_state.last_urls = {}
                    st.session_state.current_window_ref = {"handle": None}
                    st.session_state.stop_monitor = {"stop": False}
                    st.session_state.monitor_threads = []
                    # --- CLEAR action buffers so this recording starts fresh ---
                    st.session_state.actions = []
                    st.session_state.workflow_text = []
                    st.session_state.recorded_script = None
                    st.session_state.rb_actions_snapshot = []
                    handle=st.session_state.driver.current_window_handle
                    st.session_state.driver.execute_script(action_utils.injection_script_agentflow())
                    print(f"✅ JS injected in new window {handle} ({st.session_state.driver.current_url})")
                    st.session_state.injected_windows[handle] = True
                    # --- Thread 1: New windows checker ---
                    t1 = threading.Thread(
                        target=utils.thread_new_window_checker,
                        args=(
                            st.session_state.driver,
                            st.session_state.injected_windows,
                            st.session_state.last_urls,
                            st.session_state.stop_monitor,
                            page_screenshot_folder,
                            st.session_state.current_window_ref
                        ),
                        daemon=True
                    )

                    # --- Thread 2: Focus and URL monitor ---
                    t2 = threading.Thread(
                        target=utils.thread_focus_and_url_monitor,
                        args=(
                            st.session_state.driver,
                            st.session_state.injected_windows,
                            st.session_state.last_urls,
                            st.session_state.stop_monitor,
                            page_screenshot_folder,
                            st.session_state.current_window_ref
                        ),
                        daemon=True
                    )
                    t3 = threading.Thread(
                        target=utils.thread_focus_screenshot,
                        args=(
                            st.session_state.driver,
                            st.session_state.stop_monitor,
                            page_screenshot_folder,source

                        ),
                        daemon=True
                    )
                    t4 = threading.Thread(
                        target=utils.thread_reinject_action_check,
                        args=(
                            st.session_state.driver,
                            st.session_state.stop_monitor,
                            st.session_state.last_urls, st.session_state.current_window_ref,
                            st.session_state.injected_windows

                        ),
                        daemon=True
                    )
                    # --- Start threads ---
                    t1.start()
                    t2.start()
                    t3.start()
                    t4.start()

                    st.session_state.monitor_threads = [t1, t2,t3,t4]

                    st.session_state.recording_started = True
                    st.success("Recording started. Please interact in the browser.")
            if st.session_state.recording_started and st.button("🛑 Stop Recording"):

                st.session_state.actions = action_utils.get_recorded_actions(
                    st.session_state.driver)
                # Snapshot for Record & Playback — survives the post-save actions.clear()
                st.session_state.rb_actions_snapshot = list(st.session_state.actions)
                st.session_state.recording_started = False

                # Signal all threads to stop
                st.session_state.stop_monitor["stop"] = True

                # Join all monitor threads — timeout=2 is enough since threads now use
                # 0.5s sleep chunks and check stop_flag between each chunk
                for t in st.session_state.get("monitor_threads", []):
                    if t and t.is_alive():
                        t.join(timeout=2)

                # Clear thread references for next start
                st.session_state.monitor_threads = []
                st.success("Recording stopped. Performed actions are captured.")
                actions = []
                st.session_state.injected_windows.clear()
            # 4. Show and Save Actions
            if st.session_state.actions:
                st.session_state.workflow_text = []
                page_name = st.text_input("Enter Page Name for Saving the Workflow:")
                if st.button("💾 Save Workflow"):

                    if not page_name:
                        st.warning("⚠ Please enter a name for the workflow.")
                    else:
                        st.session_state.workflow_text = action_utils.generate_workflow_manual(st.session_state.actions)
                        workflow_saved = False
                        print("workflow_text",st.session_state.workflow_text)
                        if source == "database":
                            action_id = db_handler.save_action_to_db(page_name,st.session_state.workflow_text , get_update_user())
                            st.success(f"✅ Action saved to database (ID: {action_id})")
                            #st.write(db_handler.get_action_file_by_name(page_name))
                        elif source == "file":
                            filename = os.path.join(Action_collection, f"{page_name}_actions.txt")
                            def clean_text(s):
                                return (
                                    s.replace("\u200b", "")
                                    .replace("\xa0", " ")
                                    .strip()
                                )
                            cleaned = [clean_text(x) for x in st.session_state.workflow_text]
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write("\n".join(cleaned))
                            # with open(filename, "w") as f:
                            #     f.write("\n".join(st.session_state.workflow_text ))  # ✅ FIXED
                                 #f.write(st.session_state.workflow_text)
                            st.success(f"✅ Workflow saved: {filename}")
                            #action_utils.reinject_clear_local_storage(st.session_state.driver)
                            st.download_button("⬇ Download Workflow", data="\n".join(st.session_state.workflow_text ),
                                            file_name=f"{page_name}_actions.txt")
                            workflow_saved = True
                        if  workflow_saved:
                            clear_actions = """(function() {
                                            window.__recordedActions = [];
                                            localStorage.removeItem("recordedActions");
                                            console.log("🧹 Cleared previous recorded actions before new recording session.");
                                        })();"""
                            st.session_state.driver.execute_script(clear_actions)
                            st.session_state.actions.clear()
                            st.session_state.workflow_text.clear()
                            st.session_state.show_popup = True
                            st.session_state.show_form = False

        if option == 'Desktop':

            st.subheader("Record User Actions & Capture Screenshots of User Navigation")

            # FIX: use a SEPARATE session state key for desktop recording
            # so it doesn't conflict with st.session_state.recording_started
            # used by the Web recorder tab.
            if "desktop_recording_started" not in st.session_state:
                st.session_state.desktop_recording_started = False
            if "recorder" not in st.session_state:
                st.session_state.recorder = None

            application_path = st.text_input(
                "Enter full path to application (.exe):",
                placeholder=r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
            )

            # ── START ──────────────────────────────────────────────────────────
            if application_path and not st.session_state.desktop_recording_started:
                if st.button("🎥 Launch and Start Recording"):
                    with st.spinner("Launching application, please wait..."):
                        try:
                            session = DesktopSession(application_path)
                            app = session.start(timeout=15)  # waits for window ready

                            recorder = DesktopRecorder()
                            recorder.start()

                            st.session_state.recorder = recorder
                            st.session_state.desktop_recording_started = True
                            st.rerun()

                        except Exception as e:
                            st.error(f"Failed to launch application: {e}")

            # ── RECORDING IN PROGRESS ─────────────────────────────────────────
            if st.session_state.desktop_recording_started:
                st.info("🔴 Recording in progress... Interact with the application, then click Stop.")

                if st.button("🛑 Stop Recording"):
                    st.session_state.recorder.stop()
                    st.session_state.desktop_recording_started = False
                    action_count = len(st.session_state.recorder.get_actions())
                    st.success(f"✅ Recording stopped. {action_count} action(s) captured.")
                    st.rerun()

            # ── SAVE ──────────────────────────────────────────────────────────
            if (not st.session_state.desktop_recording_started
                    and st.session_state.recorder
                    and st.session_state.recorder.get_actions()):

                workflow_name = st.text_input("Enter name for saving the workflow:")

                if workflow_name:
                    if st.button("💾 Save Desktop Workflow"):
                        file_name = workflow_name
                        st.session_state.workflow_text_desktop=st.session_state.recorder.save(file_name)
                        filename = os.path.join(Action_collection_desktop, f"{file_name}_desktop_actions.txt")
                        def clean_text(s):
                            return (
                                s.replace("\u200b", "")
                                .replace("\xa0", " ")
                                .strip()
                            )
                        cleaned = [clean_text(x) for x in st.session_state.workflow_text_desktop]
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write("\n".join(cleaned))
                        st.success(f"✅ Workflow saved: {filename}")
                        st.download_button("⬇ Download Workflow", data="\n".join(st.session_state.workflow_text_desktop),
                                           file_name=f"{file_name}_actions.txt")
                        st.session_state.recorder = None
                        st.session_state.workflow_text_desktop=[]

        # ── Record & Playback: Quick Script Generator ─────────────────────
        if st.session_state.rb_actions_snapshot:
            with st.expander("⚡ Quick Script Generator (Record & Playback)", expanded=False):
                st.caption(
                    "Generate an automation script directly from your recorded actions — "
                    "no page file or test case needed."
                )
                st.session_state.rb_language  = st.selectbox(
                    "Select target language / framework",
                    ["Python-Selenium", "Python-Playwright", "Java-Selenium", "Java-Playwright", "UTAM-JavaScript"],
                    key="rb_language_select"
                )
                rb_script_name = st.text_input("Script file name (without extension):", key="rb_script_name")

                if st.button("⚡ Generate Script from Recording", key="rb_generate_btn"):
                    with st.spinner("Generating script from recorded actions..."):
                        actions_formatted = action_utils.format_actions_for_script_generation(
                            st.session_state.rb_actions_snapshot
                        )
                        script = utils.generate_script_from_recorded_actions(actions_formatted, st.session_state.rb_language )
                        if script:
                            st.session_state.recorded_script = script
                            st.session_state.recorded_script_language = st.session_state.rb_language 
                            st.success("✅ Script generated from recording.")
                        else:
                            st.error("Failed to generate script from recording.check the error logs")
                    

                if st.session_state.recorded_script:
                    _rb_lang = st.session_state.recorded_script_language
                    _code_lang = (
                        "java" if "java" in _rb_lang.lower()
                        else ("javascript" if "javascript" in _rb_lang.lower() else "python")
                    )
                    st.subheader("📝 Generated Script")
                    st.code(st.session_state.recorded_script, language=_code_lang)

                    with st.expander("✏️ Edit before saving", expanded=False):
                        st.text_area(
                            "Edit the script:",
                            value=st.session_state.recorded_script,
                            key="rb_script_editor",
                            height=500
                        )

                    if st.button("💾 Save Script", key="rb_save_btn"):
                        if not rb_script_name:
                            st.warning("Please enter a script file name.")
                        else:
                            final_rb_script = st.session_state.get(
                                "rb_script_editor", st.session_state.recorded_script
                            )
                            utils.create_test_file(Test_file_generator, rb_script_name,
                                                   _rb_lang, final_rb_script)
                            st.success(f"✅ Script saved: {rb_script_name}")
        # ── End Record & Playback ──────────────────────────────────────────

        # if option == 'Desktop':
        #
        #     st.subheader("Record User Actions & Capture Screenshots of User Navigation")
        #
        #     # # Initialize session state variables
        #     # if "recorder" not in st.session_state:
        #     #     st.session_state.recorder = None
        #
        #     if "recording_started" not in st.session_state:
        #         st.session_state.recording_started = False
        #
        #     application_name = st.text_input("Enter application Name for Saving the Workflow:")
        #
        #     # -----------------------------
        #     # Start Recording
        #     # -----------------------------
        #     if application_name and not st.session_state.recording_started:
        #         if st.button("🎥 Launch and Start Recording"):
        #             session = DesktopSession(application_name)
        #             app = session.start()
        #
        #             recorder = DesktopRecorder()
        #             recorder.start()
        #
        #             st.session_state.recorder = recorder
        #             st.session_state.recording_started = True
        #
        #             st.success("Recording started. Please interact with the application.")
        #
        #     # -----------------------------
        #     # Stop Recording
        #     # -----------------------------
        #     if st.session_state.recording_started:
        #
        #         if st.button("🛑 Stop Recording"):
        #             st.session_state.recorder.stop()
        #             st.session_state.recording_started = False
        #
        #             st.success("Recording stopped.")
        #
        #             st.session_state.desktop_action_name = ""
        #
        #     # -----------------------------
        #     # Save Workflow
        #     # -----------------------------
        #     if not st.session_state.recording_started and st.session_state.recorder:
        #
        #         workflow_name = st.text_input("Enter Name for Saving the Workflow:")
        #
        #         if workflow_name:
        #             if st.button("💾 Save Desktop Workflow"):
        #                 file_name = workflow_name + ".txt"
        #                 st.session_state.recorder.save(file_name)
        #
        #                 st.success(f"Workflow saved as {file_name}")
if st.session_state.checkbox2_state:
    with st.expander("🧾 BDD Feature File Generator"):
        st.title("Feature file Generator using recorded actions")
        Feature_file_name = st.text_input("Enter feature file Name")
        Action_data = ""
        if source == "file":
            Action_data = utils.select_and_read_text_files(Action_collection)
        elif source == "database":
            all_files = db_handler.get_all_action_names()
            selected_files = st.multiselect("Feature - Select saved action files from database", all_files)

            if selected_files:
                merged_content = ""

                for file in selected_files:
                    content = db_handler.get_action_content_by_name(file, "action")
                    if content:
                        merged_content += f"\n### {file} ###\n{content}\n"
                    else:
                        st.warning(f"⚠️ Could not load content for: {file}")
                Action_data = merged_content
        # if source =="file":
        # Action_data = utils.select_and_read_text_files_xpath("feature",Action_collection)
        action_prompt = f"""Summarize the following context into a concise and structured format (under 100 lines), preserving key actions, entities, and sequences. The goal is to retain essential meaning for AI understanding, automation, or test case generation. Avoid repetition, and group related items logically. Context: {Action_data} """
        action_data_processed = utils.get_queries_from_ai_updated(action_prompt)
        feature_prompt = utils.generate_pom_from_excel_feature("Feature_file", action_data_processed)
        if st.button("Generate_feature_File"):
            feature_response=utils.get_queries_from_ai_updated(feature_prompt)
            if source == "file":
                save_feature_file = os.path.join(feature_file_collection, f"{Feature_file_name}.feature")
                with open(save_feature_file, "w") as file:
                    file.write(feature_response.strip())

                st.write(f"Feature file saved here: {save_feature_file}")
            if source == "database":
                db_handler.save_featurefile_to_db(Feature_file_name, feature_response, get_update_user())
                st.success(f"feature file save in database for '{Feature_file_name}'")
if st.session_state.checkbox3_state:
    with (st.expander("🧮 E2E Scenario Based Test Case Generator")):

        st.title("E2E Scenario Based Test Case Generation")

        option = st.radio(
            "Choose your Flow with:",
            ('Documents', 'Recorded_Details')
        )

        if option == 'Recorded_Details':
            # Show image selection and prompt box
            if source == "file":
                st.markdown("**Select Images (Mandatory)** <span style='color:red;'>*</span>", unsafe_allow_html=True)
                image_files = [f for f in os.listdir(page_screenshot_folder) if
                               f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
                cols = st.columns(5)
                for idx, image_file in enumerate(image_files):
                    with cols[idx % 5]:
                        st.image(os.path.join(page_screenshot_folder, image_file), width=100)
                        if image_file not in st.session_state.selected_images:
                            if st.button(f"{image_file}", key=f"{image_file}"):
                                st.session_state.selected_images.append(image_file)
                        else:
                            if st.button(f"Deselect {image_file}", key=f"deselect_{image_file}"):
                                st.session_state.selected_images.remove(image_file)
            if source == "database":
                st.markdown("**Select Images from database (Mandatory)** <span style='color:red;'>*</span>",
                            unsafe_allow_html=True)

                screenshots = db_handler.get_all_screenshots()  # session from SQLAlchemy

                if not screenshots:
                    st.warning("⚠️ No images found in the database.")
                else:
                    cols = st.columns(5)

                    for idx, screenshot in enumerate(screenshots):
                        with cols[idx % 5]:
                            image = Image.open(io.BytesIO(screenshot.image_data))

                            # Optional: Resize to thumbnail
                            max_width = 100
                            aspect_ratio = image.height / image.width
                            resized_image = image.resize((max_width, int(max_width * aspect_ratio)))

                            st.image(resized_image, use_container_width=False)

                            label = f"{screenshot.page_name}_{screenshot.id}"

                            if label not in st.session_state.selected_images:
                                if st.button(f"{label}", key=f"{label}"):
                                    st.session_state.selected_images.append(label)
                            else:
                                if st.button(f"Deselect {label}", key=f"deselect_{label}"):
                                    st.session_state.selected_images.remove(label)

            if st.session_state.selected_images:
                    st.write("### Selected images in order:")
                    for i, img_name in enumerate(st.session_state.selected_images, 1):
                        st.write(f"{i}. {img_name}")

            if st.button("Clear All Selection"):
                st.session_state.selected_images = []

            st.markdown("**Upload Wireframe / Additional Images (Optional)**", unsafe_allow_html=True)
            wireframe_uploads = st.file_uploader(
                "Upload wireframe or additional images",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="wireframe_image_uploader"
            )
            if wireframe_uploads:
                for wf_file in wireframe_uploads:
                    save_path = os.path.join(page_screenshot_folder, wf_file.name)
                    with open(save_path, "wb") as f:
                        f.write(wf_file.getbuffer())
                    if wf_file.name not in st.session_state.selected_images:
                        st.session_state.selected_images.append(wf_file.name)
                st.success(f"{len(wireframe_uploads)} wireframe image(s) added to selection.")

            st.markdown("**Enter the additional information or requirements** <span style='color:red;'>*</span>",
                        unsafe_allow_html=True)
            prompt = st.text_area("Enter the test requirements", "",key="user_requirements_textarea")
            st.markdown("**Please select relevent action file(Optional)**", unsafe_allow_html=True)
            Action_data = ""
            if source == "file":
                Action_data = utils.select_and_read_text_files(Action_collection)
            elif source == "database":
                all_files=db_handler.get_all_action_names()
                selected_files = st.multiselect("Select saved action files from database", all_files)

                if selected_files:
                    merged_content = ""

                    for file in selected_files:
                        content = db_handler.get_action_content_by_name(file,"action")
                        if content:
                            merged_content += f"\n### {file} ###\n{content}\n"
                        else:
                            st.warning(f"⚠️ Could not load content for: {file}")
                    Action_data = merged_content
        elif option == 'Documents':
            source_type = st.selectbox(
                "Select Source Type",
                options=["Files", "Azure Board", "Jira"],
                index=0,  # ensures default selection is "Files"
            )
            # store selection explicitly (optional, selectbox with key already updates session_state)
            st.session_state.document_source_selector = source_type
            # Show only document upload section
            if source_type == "Files":
            # Show only document upload section
                uploaded_file = st.file_uploader(
                    "Upload a PDF, Text, Word, or Excel document",
                    type=['pdf', 'docx', 'xlsx', 'txt'],
                    key="uploaded_file_uploader"  # this will populate st.session_state.uploaded_file_uploader
                )
                if uploaded_file is not None:
                    filename = uploaded_file.name.lower()

                    if filename.endswith(".pdf"):
                        st.success("PDF file uploaded successfully!")
                        # Call your PDF extraction logic here
                        # extracted_text = utils.extract_text_from_document(uploaded_file, filename)

                    elif filename.endswith(".docx"):
                        st.success("Word file uploaded successfully!")
                        # Call your DOCX extraction logic here

                    elif filename.endswith(".xlsx"):
                        st.success("Excel file uploaded successfully!")
                        # Call your Excel extraction logic here

                    elif filename.endswith(".txt"):
                        st.success("Text file uploaded successfully!")
                        try:
                            text_content = uploaded_file.read().decode("utf-8", errors="ignore")
                        except Exception as e:
                            st.error(f"Error reading TXT file: {e}")

                    else:
                        # This branch should rarely hit because file_uploader already restricts type
                        st.error("Unsupported file format.")
            elif source_type == "Azure Board":
                st.info("Enter Azure Work Item ID (numeric)")
                workitem = st.text_input("Azure Work Item ID", value=st.session_state.azure_workitem_id,
                                         key="azure_workitem_text")
                st.session_state.azure_workitem_id = workitem.strip()

                if workitem and not workitem.isdigit():
                    st.warning("Work Item ID typically numeric — ensure it's correct.")

            elif source_type == "Jira":
                st.info("Enter Jira Issue ID (e.g. PROJ-123)")
                jira_id = st.text_input("Jira Issue ID", value=st.session_state.jira_workitem_id,
                                        key="jira_workitem_text")
                st.session_state.jira_workitem_id = jira_id.strip()
            Document_image_data = ""
            image_uploaded_files = st.file_uploader(
                "📁 Upload one or more image files (Optional)",
                type=["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
                accept_multiple_files=True
            )
            if image_uploaded_files:
                st.info("📸 Image processed.")
                for image_uploaded_file in image_uploaded_files:
                    try:
                        image = Image.open(image_uploaded_file)
                        #st.image(image, caption=uploaded_file.name, use_container_width=True)

                        # Extract text using pytesseract
                        extracted_text = pytesseract.image_to_string(image)
                        if extracted_text.strip():
                            Document_image_data += f"\nImage: {image_uploaded_file.name}\nExtracted Text:\n{extracted_text.strip()}\n"
                        else:
                            Document_image_data += f"\nImage: {image_uploaded_file.name}\nExtracted Text: No text found\n"

                    except Exception as e:
                        st.error(f"Error processing {image_uploaded_file.name}: {e}")
            
            st.markdown("Enter the navigation details (Optional)",
                        unsafe_allow_html=True)
            Navigation_details = st.text_area("Enter Navigation Details", "",key="navigation_details_textarea")

        # ── Test Management Tool Integration ──────────────────────────────────
        with st.expander("🔗 Test Management Integration (Optional)", expanded=False):
            st.caption("Connect to Azure Test Plans or Jira to fetch existing test cases and run a gap analysis before generation.")
            tmt_tool = st.radio(
                "Select Test Management Tool",
                options=["None", "Azure Test Plans", "Jira"],
                horizontal=True,
                key="tmt_tool_radio"
            )
            st.session_state.tmt_tool = tmt_tool

            if tmt_tool == "Azure Test Plans":
                col_az1, col_az2 = st.columns(2)
                with col_az1:
                    st.text_input("Organization URL", value="https://dev.azure.com/QE-Practice-team", key="tmt_az_org", disabled=True)
                with col_az2:
                    st.text_input("Project", value="qe-practice", key="tmt_az_project", disabled=True)

                # Type selector — Test Plan requires test plan license; Test Cases works on all tiers
                fetch_type = st.selectbox(
                    "Fetch Type",
                    options=["Test Cases", "Test Plan"],
                    index=0 if st.session_state.tmt_fetch_type == "Test Cases" else 1,
                    key="tmt_fetch_type_select",
                    help="Select 'Test Cases' if you don't have a Test Plans license (trial accounts). Select 'Test Plan' to fetch via a specific plan and suite."
                )
                st.session_state.tmt_fetch_type = fetch_type

                if fetch_type == "Test Cases":
                    # Direct WIQL fetch — no test plan required
                    if st.button("📥 Fetch Test Cases Directly"):
                        with st.spinner("Fetching test cases from project..."):
                            try:
                                tcs = tmt_utils.get_all_testcases_direct()
                                st.session_state.tmt_existing_tcs = tcs
                                st.session_state.tmt_connected = True
                                st.success(f"✅ Fetched {len(tcs)} test case(s) directly from project.")
                            except Exception as e:
                                st.error(f"❌ Fetch failed: {e}")
                                st.session_state.tmt_connected = False

                else:
                    # Test Plan flow — requires test plan license
                    if st.button("🔌 Connect & Fetch Test Plans"):
                        with st.spinner("Fetching test plans..."):
                            try:
                                st.session_state.tmt_plans = tmt_utils.get_test_plans()
                                st.session_state.tmt_connected = True
                                st.success(f"✅ Connected — {len(st.session_state.tmt_plans)} test plan(s) found.")
                            except Exception as e:
                                st.error(f"❌ Connection failed: {e}")
                                st.session_state.tmt_connected = False

                    if st.session_state.tmt_connected and st.session_state.tmt_plans:
                        plan_options = {p["name"]: p["id"] for p in st.session_state.tmt_plans}
                        selected_plan_name = st.selectbox("Select Test Plan", options=list(plan_options.keys()), key="tmt_plan_select")
                        st.session_state.tmt_selected_plan_id = plan_options[selected_plan_name]

                        scope = st.radio("Scope", ["All Suites", "Specific Suite"], horizontal=True, key="tmt_scope_radio")
                        if scope == "Specific Suite":
                            if st.button("Load Suites"):
                                st.session_state.tmt_suites = tmt_utils.get_test_suites(st.session_state.tmt_selected_plan_id)
                            if st.session_state.tmt_suites:
                                suite_options = {s["name"]: s["id"] for s in st.session_state.tmt_suites}
                                selected_suite_name = st.selectbox("Select Suite", options=list(suite_options.keys()), key="tmt_suite_select")
                                st.session_state.tmt_selected_suite_id = suite_options[selected_suite_name]
                        else:
                            st.session_state.tmt_selected_suite_id = None

                        if st.button("📥 Fetch Existing Test Cases"):
                            with st.spinner("Fetching existing test cases..."):
                                try:
                                    if st.session_state.tmt_selected_suite_id:
                                        tcs = tmt_utils.get_testcases_from_suite(
                                            st.session_state.tmt_selected_plan_id,
                                            st.session_state.tmt_selected_suite_id
                                        )
                                    else:
                                        tcs = tmt_utils.get_all_testcases_from_plan(
                                            st.session_state.tmt_selected_plan_id
                                        )
                                    st.session_state.tmt_existing_tcs = tcs
                                    st.success(f"✅ Fetched {len(tcs)} existing test case(s).")
                                except Exception as e:
                                    st.error(f"❌ Failed to fetch test cases: {e}")

            elif tmt_tool == "Jira":
                col_j1, col_j2 = st.columns(2)
                with col_j1:
                    jira_project = st.text_input("Jira Project Key (e.g. QA)", key="tmt_jira_project_input")
                    st.session_state.tmt_jira_project_key = jira_project.strip()

                if st.button("📥 Fetch Jira Test Cases"):
                    with st.spinner("Fetching Jira test cases..."):
                        try:
                            tcs = tmt_utils.get_jira_testcases(st.session_state.tmt_jira_project_key)
                            st.session_state.tmt_existing_tcs = tcs
                            st.session_state.tmt_connected = True
                            st.success(f"✅ Fetched {len(tcs)} Jira test case(s).")
                        except Exception as e:
                            st.error(f"❌ Jira fetch failed: {e}")

            if st.session_state.tmt_existing_tcs:
                st.info(f"📋 {len(st.session_state.tmt_existing_tcs)} existing test case(s) loaded — gap analysis will run before generation.")
                with st.expander("Preview existing test cases"):
                    for tc in st.session_state.tmt_existing_tcs[:10]:
                        st.write(f"**{tc['id']}** — {tc['title']}")
                    if len(st.session_state.tmt_existing_tcs) > 10:
                        st.caption(f"...and {len(st.session_state.tmt_existing_tcs) - 10} more")
            else:
                st.caption("No existing test cases loaded — generation will proceed without gap analysis.")
        # ─────────────────────────────────────────────────────────────────────

        if st.button("Generate Functional Test Cases"):
            st.session_state.testcase_response = []
            st.session_state.testcases_saved = False
            st.session_state.scenario_response = None
            st.session_state.all_testcases= None
            st.session_state.overall_accuracy = None
            st.session_state.testcase_regeneration = None
            st.session_state.save_testcases = False
            st.session_state.regenerate_clicked = False
            st.session_state.save_regenerated_testcases = False
            #st.session_state.all_responses = []
            # st.write(Action_data)
            if option == 'Recorded_Details':
                if st.session_state.selected_images and prompt:
                    # Construct navigation as a comma-separated string
                    navigation = ', '.join(st.session_state.selected_images)
                    # st.write(navigation)

                    # Finding images in the pages folder and extracting text using pytesseract
                    image_data = ""
                    if source == "file":
                        for image_name in st.session_state.selected_images:
                            image_path = os.path.join(page_screenshot_folder, image_name)
                            if os.path.exists(image_path):
                                image = Image.open(image_path)
                                st.image(image, caption=image_name, use_container_width=True)

                                try:
                                    extracted_text = pytesseract.image_to_string(image)
                                    if extracted_text:
                                        image_data += f"\nImage: {image_name}\nExtracted Text: {extracted_text}\n"
                                    else:
                                        image_data += f"\nImage: {image_name}\nExtracted Text: No text found\n"
                                except Exception as e:
                                    st.error(f"Error extracting text from {image_name}: {e}")
                            else:
                                st.error(f"Image not found: {image_name}")

                    elif source == "database":
                        screenshots = db_handler.get_all_screenshots()

                        # Use a lookup dictionary for faster access
                        db_image_map = {f"{s.page_name}_{s.id}": s.image_data for s in screenshots}

                        for image_key in st.session_state.selected_images:
                            if image_key in db_image_map:
                                try:
                                    image = Image.open(io.BytesIO(db_image_map[image_key]))
                                    st.image(image, caption=image_key, use_container_width=True)

                                    extracted_text = pytesseract.image_to_string(image)
                                    if extracted_text:
                                        image_data += f"\nImage: {image_key}\nExtracted Text: {extracted_text}\n"
                                    else:
                                        image_data += f"\nImage: {image_key}\nExtracted Text: No text found\n"
                                except Exception as e:
                                    st.error(f"Error extracting text from {image_key}: {e}")
                            else:
                                st.error(f"Image not found in database: {image_key}")
                    image_prompt = f"""Summarize the following context into a concise and structured format (under 100 lines), preserving key actions, entities, and sequences. The goal is to retain essential meaning for AI understanding, automation, or test case generation. Avoid repetition, and group related items logically. Context: {image_data} """
                    print(image_prompt)
                    image_data_processed = utils.get_queries_from_ai_updated(image_prompt) or image_data
                    print(image_data_processed)
                    if not Action_data:
                        Action_data = None

                    # ── BLOCK 1: Gap Analysis — runs on Generate click, stores in session state ──
                    if st.session_state.tmt_existing_tcs:
                        with st.spinner("🔍 Running gap analysis against existing test cases..."):
                            gap_result = utils.analyze_testcase_gaps(
                                st.session_state.tmt_existing_tcs,
                                Action_data,
                                image_data_processed,
                                prompt
                            )
                        # Store gap result + all inputs needed for generation after approval
                        st.session_state.gap_analysis_result = gap_result
                        st.session_state.tmt_gap_approved = False
                        st.session_state.tmt_replacement_responses = ""
                        st.session_state.tmt_deletion_notice = []
                        st.session_state.tmt_gen_inputs = {
                            "navigation": navigation,
                            "image_data_processed": image_data_processed,
                            "Action_data": Action_data,
                            "prompt": prompt
                        }
                        # Don't generate yet — wait for user approval (handled in BLOCK 2 below)
                    else:
                        # No TMT connected — generate directly and show category summary
                        if model_type == "azureopenai":
                            constructedprompt = utils.generate_pom_from_excel_testcases(
                                "Test_case_generation", navigation, image_data_processed, Action_data, prompt)
                        else:
                            constructedprompt = utils.generate_pom_from_excel_testcases(
                                "Test_case_generation_gemini", navigation, image_data_processed, Action_data, prompt)
                        st.session_state.testcase_response = utils.generate_testcases_with_dynamic_stop(constructedprompt, 15, 5)
                        utils.parse_and_display_testcases_categorywise(st.session_state.testcase_response)
                    # ──────────────────────────────────────────────────────────────────────

                    # if model_type == "azureopenai":
                    #     print("Model Type is AzureOpenAi - chunked generation")
                    #     st.session_state.testcase_response = utils.generate_testcases_with_chunking(
                    #         navigation, image_data_processed, Action_data, prompt,
                    #         prompt_type="Test_case_generation"
                    #     )
                    # else:
                    #     print("Model Type is pepgenx")
                    #     constructedprompt = utils.generate_pom_from_excel_testcases("Test_case_generation_gemini", navigation,
                    #                                                                 image_data_processed, Action_data,
                    #                                                                 prompt)
                    #     print("******final prompt *******")
                    #     st.session_state.testcase_response = utils.generate_testcases_with_dynamic_stop(constructedprompt, 25, 5)
                    # #st.code(st.session_state.testcase_response)
            elif option == 'Documents' and source_type is not None:

                if source_type == "Files" and uploaded_file is not None:
                    extracted_data = utils.extract_text_from_document(uploaded_file,uploaded_file.name)
                elif source_type == "Azure Board" and st.session_state.azure_workitem_id is not None:
                    try:
                        exists, message = tmt_utils.validate_work_item_exists(st.session_state.azure_workitem_id)
                        if exists:
                            extracted_data = tmt_utils.fetch_workitem_detail(st.session_state.azure_workitem_id)
                        else:
                            st.error(message)
                            st.error("Please enter valid workitem")
                            st.stop()
                    except Exception as e:
                        st.error("Invalid Work Item")
                elif source_type == "Jira"and st.session_state.jira_workitem_id is not None:
                    try:
                        exists, message = tmt_utils.validate_work_item_exists(st.session_state.jira_workitem_id )
                        if exists:

                            extracted_data = tmt_utils.fetch_workitem_detail(st.session_state.jira_workitem_id)
                        else:
                            st.error(message)
                            st.error("Please enter valid workitem")
                            st.stop()
                    except Exception as e:
                        st.error("Invalid Work Item")
                image_prompt = f"""Summarize the following context into a concise and structured format (under 100 lines), preserving key actions, entities, and sequences. The goal is to retain essential meaning for AI understanding, automation, or test case generation. Avoid repetition, and group related items logically. Context: {Document_image_data} """
                if model_type == "azureopenai":
                    Document_image_data_processed = utils.get_queries_from_ai_updated(image_prompt)
                else:
                    Document_image_data_processed = utils.llm_pepgenx(image_prompt)
                print(Document_image_data_processed)

                st.session_state.testcase_response = []
                st.session_state.scenario_response = []
                st.session_state.all_testcases = []
                # scenarios_prompt=utils.generate_excel_testcases_with_document("Test_scenarios_finder",extracted_data,Document_image_data_processed,Navigation_details)
                # st.session_state.scenario_response=utils.get_queries_from_ai_updated(scenarios_prompt)
                # st.write(st.session_state.scenario_response)
                if model_type == "azureopenai":
                    print("Model Type is AzureOpenAi")
                    constructedprompt = utils.generate_excel_testcases_with_document("Test_case_generation_document",
                                                                                     extracted_data,Document_image_data_processed,Navigation_details)
                else:
                    print("Model Type is gimini")
                    constructedprompt = utils.generate_excel_testcases_with_document("Test_case_generation_document_gemini",
                                                                                 extracted_data)
                st.session_state.testcase_response = utils.generate_testcases_with_dynamic_stop(constructedprompt,120,5)
                #st.code(st.session_state.testcase_response)
                # test_categories=utils.categorize_testcases_with_full_requirements(st.session_state.all_testcases  , extracted_data,Document_image_data_processed,Navigation_details)
                # ui_display=utils.format_categories_for_ui(test_categories)
                utils.parse_and_display_testcases_categorywise(st.session_state.testcase_response)

        # ── BLOCK 2: Show gap analysis results + Approve button (persisted in session state) ──
        if st.session_state.gap_analysis_result and not st.session_state.tmt_gap_approved:
            gap_result = st.session_state.gap_analysis_result
            st.markdown("### 📊 Gap Analysis Result")
            col_g1, col_g2, col_g3 = st.columns(3)
            col_g1.metric("🆕 New Scenarios", len(gap_result["new"]))
            col_g2.metric("✏️ Need Replacement", len(gap_result["update"]))
            col_g3.metric("✅ Already Covered", len(gap_result["skip"]))

            if gap_result["new"]:
                with st.expander("🆕 New scenarios to generate"):
                    for i, scenario in enumerate(gap_result["new"], 1):
                        st.write(f"{i}. {scenario}")

            if gap_result["update"]:
                with st.expander("✏️ Test cases to be replaced (you will be asked to delete originals manually)"):
                    for item in gap_result["update"]:
                        st.write(f"**{item['id']}** — {item['title']}")
                        st.caption(f"Reason: {item['reason']}")

            if st.button("✅ Approve & Generate"):
                st.session_state.tmt_gap_approved = True
                st.rerun()

        # ── BLOCK 3: Actual generation — runs after approval, survives reruns ──
        if st.session_state.tmt_gap_approved and st.session_state.gap_analysis_result and not st.session_state.testcase_response:
            gap_result = st.session_state.gap_analysis_result
            inputs = st.session_state.tmt_gen_inputs
            navigation = inputs.get("navigation", "")
            image_data_processed = inputs.get("image_data_processed", "")
            Action_data = inputs.get("Action_data", None)
            prompt = inputs.get("prompt", "")

            # ── Targeted generation: exactly one TC per new scenario ────────────
            # Uses a single focused LLM call — NOT the iterative dynamic stop
            # which would generate 15-20 TCs regardless of what gap analysis found
            if gap_result["new"]:
                with st.spinner(f"Generating {len(gap_result['new'])} new test case(s)..."):
                    st.session_state.testcase_response = utils.generate_targeted_testcases(
                        scenarios=gap_result["new"],
                        action_data=Action_data,
                        image_data=image_data_processed,
                        requirements=prompt
                    )
                st.success(f"✅ {len(gap_result['new'])} new test case(s) generated.")
            else:
                st.session_state.testcase_response = ""
                st.info("No new scenarios from gap analysis — only replacements will be generated.")

            # Generate replacement test cases for update list
            if gap_result["update"]:
                st.info(f"Generating {len(gap_result['update'])} replacement test case(s)...")
                replacement_combined = ""
                deletion_notice = []
                for item in gap_result["update"]:
                    with st.spinner(f"Replacing: {item['title']}..."):
                        replacement = utils.generate_replacement_testcase(
                            title=item["title"],
                            reason=item["reason"],
                            action_data=Action_data,
                            image_data=image_data_processed,
                            requirements=prompt
                        )
                    if replacement:
                        replacement_combined += "\n" + replacement
                        deletion_notice.append(item)
                        st.success(f"✅ Replacement generated for: {item['title']}")
                    else:
                        st.warning(f"⚠️ Could not generate replacement for: {item['title']}")
                st.session_state.tmt_replacement_responses = replacement_combined
                st.session_state.tmt_deletion_notice = deletion_notice

                # Merge replacement TCs into the response
                if replacement_combined:
                    st.session_state.testcase_response = (
                        st.session_state.testcase_response + "\n" + replacement_combined
                    )

            utils.parse_and_display_testcases_categorywise(st.session_state.testcase_response)
        # ──────────────────────────────────────────────────────────────────────────────────

        if st.session_state.testcase_response:
            st.session_state.save_testcases = True
        if st.session_state.save_testcases and st.button("💾 Save test cases"):

            utils.covert_response_to_testcases_single_file(st.session_state.testcase_response, Test_case_collection)
            #utils.covert_response_to_testcases(st.session_state.testcase_response, Test_case_collection)
            st.session_state.excel_path=utils.covert_response_to_testcases_single_sheet(st.session_state.testcase_response, Test_case_collection)
            st.session_state.testcases_saved = True
            st.session_state.show_popup = True
            st.session_state.show_form = False

        # ── Deletion notification for replaced TCs ────────────────────────────
        if st.session_state.get("testcases_saved") and st.session_state.tmt_deletion_notice:
            st.warning("⚠️ The following existing test cases were replaced by newly generated ones. Please **delete them manually** from Azure DevOps:")
            for item in st.session_state.tmt_deletion_notice:
                st.markdown(f"- **{item['id']}** | {item['title']} — _{item['reason']}_")
        # ─────────────────────────────────────────────────────────────────────

        # ── TMT connected: push individual Test Case work items to Azure ─────────
        if st.session_state.get("testcases_saved") and st.session_state.tmt_existing_tcs:
            gap = st.session_state.gap_analysis_result or {}
            new_count = len(gap.get("new", []))
            update_count = len(gap.get("update", []))

            with st.expander("📤 Push to Azure DevOps", expanded=True):
                st.markdown(
                    f"Ready to push: **{new_count} new** test cases | "
                    f"**{update_count} replacement** test cases as individual Azure DevOps Test Case work items."
                )

                user_story_id = st.text_input(
                    "User Story ID (optional) — leave blank to create test cases without a parent",
                    value="",
                    key="tmt_push_userstory_id"
                )

                if st.button("📤 Push Individual Test Cases to Azure DevOps"):
                    parent_id = user_story_id.strip() or None

                    # Validate user story if provided
                    if parent_id:
                        exists, message = tmt_utils.validate_work_item_exists(parent_id)
                        if not exists:
                            st.error(f"❌ {message}")
                            st.stop()

                    # Parse all test cases from the response
                    rows = utils.parse_testcases_from_markdown(st.session_state.testcase_response)

                    # Group rows by test case name (non-empty name = first step of each TC)
                    tc_groups = {}
                    current_name = None
                    for row in rows:
                        name = row["name"].strip()
                        if name:
                            current_name = name
                            tc_groups[current_name] = []
                        if current_name:
                            tc_groups[current_name].append(row)

                    if not tc_groups:
                        st.warning("⚠️ No test cases found to push.")
                    else:
                        push_errors = []
                        created_ids = []
                        progress = st.progress(0)
                        total = len(tc_groups)

                        for i, (tc_title, tc_rows) in enumerate(tc_groups.items(), 1):
                            try:
                                steps_xml = tmt_utils.build_steps_xml(tc_rows)
                                wi_id = tmt_utils.create_testcase_with_steps(
                                    title=tc_title,
                                    steps_xml=steps_xml,
                                    parent_id=parent_id
                                )
                                if wi_id:
                                    created_ids.append(wi_id)
                                    st.write(f"✅ Created: **{tc_title}** — Work Item ID: {wi_id}")
                                else:
                                    push_errors.append(f"Failed to create: {tc_title}")
                            except Exception as e:
                                push_errors.append(f"{tc_title}: {e}")
                            progress.progress(i / total)

                        st.success(f"✅ {len(created_ids)} of {total} test cases pushed to Azure DevOps.")
                        if push_errors:
                            for err in push_errors:
                                st.error(err)
        # ─────────────────────────────────────────────────────────────────────

        # ── No TMT: show the original export popup ────────────────────────────
        if st.session_state.get("testcases_saved") and not st.session_state.tmt_existing_tcs:
            if option == "Documents" and source_type == "Azure Board":
                if st.button("📤 Export test cases to azure Board"):
                    try:
                        sub_work_item=tmt_utils.create_test_case(st.session_state.azure_workitem_id)
                        tmt_utils.upload_attachment_to_testcase(sub_work_item,st.session_state.excel_path)
                        st.success(f"✅ Test cases were successfully exported!\n\n📄 Work Item ID: **{sub_work_item}**")
                    except Exception as e:
                        st.error("Invalid Work Item")
                    st.session_state.save_testcases = False

            elif option in ("Documents", "Recorded_Details"):
                source_key = source_type if option == "Documents" else "Recorded"
                if st.session_state.show_popup and not st.session_state.show_form:
                    st.write("**Do you want to export the generated testcases?**")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Yes", key=f"export_yes_{source_key}"):
                            st.session_state.show_popup = False
                            st.session_state.show_form = True
                    with col2:
                        if st.button("No", key=f"export_no_{source_key}"):
                            st.session_state.show_popup = False
                            st.session_state.show_form = False
                            st.session_state.xpath_for_new_page_user_info = True
                            st.rerun()

                if st.session_state.show_form:
                    st.info("Enter Work Item ID (numeric, optional)")
                    workitem = st.text_input("Work Item ID", value=st.session_state.azure_workitem_id,
                                             key="azure_workitem_text")
                    st.session_state.azure_workitem_id = workitem.strip()
                    if workitem and not workitem.isdigit():
                        st.warning("Work Item ID typically numeric — ensure it's correct.")
                    if st.button("📤 Export test cases to Azure"):
                        try:
                            if st.session_state.azure_workitem_id:
                                exists, message = tmt_utils.validate_work_item_exists(st.session_state.azure_workitem_id)
                                if exists:
                                    child_id = tmt_utils.create_test_case(st.session_state.azure_workitem_id)
                                else:
                                    st.error(f"{message} — Please enter a valid Work Item.")
                                    st.stop()
                            else:
                                child_id = tmt_utils.create_direct_test_case()
                            tmt_utils.upload_attachment_to_testcase(child_id, st.session_state.excel_path)
                            st.success(f"✅ Test cases exported — Work Item ID: **{child_id}**")
                        except Exception as e:
                            st.error(f"Export failed: {e}")
        # ─────────────────────────────────────────────────────────────────────


if st.session_state.checkbox4_state:
    with st.expander("🧪 Action-Driven Test Data Generator"):
        st.title("Enhanced Test Data Generator (Based on Action File)")
        st.session_state.test_data_action_data = ""
        st.session_state.test_files_content = ""
        if source == "file":
            st.session_state.test_files_content = utils.select_and_read_text_files_xpath("test data generation -Test Cases files", Test_case_collection)
            st.session_state.test_data_action_data = utils.select_and_read_text_files_xpath("test data generation -Recorded actions files", Action_collection)
        elif source == "database":
            all_testcase_files = db_handler.get_all_testcasefile_names()
            selected_testcase_files = st.multiselect("Select saved testcase files from database", all_testcase_files)
            if selected_testcase_files:
                merged_testcase_content = ""

                for file in selected_testcase_files:
                    content = db_handler.get_action_content_by_name(file, "testcase")
                    if content:
                        merged_testcase_content += f"\n### {file} ###\n{content}\n"
                    else:
                        # st.warning(f"⚠️ Could not load content for: {file}")
                        st.session_state.failed_files.append(file)

                st.session_state.test_files_content = merged_testcase_content
                if st.session_state.failed_files:
                    st.warning("⚠️ Could not load content for the following files:\n- " + "\n- ".join(
                        st.session_state.failed_files))
            all_files = db_handler.get_all_action_names()
            selected_files = st.multiselect("Select saved action files from database for pagefile",
                                            all_files)
            if selected_files:
                merged_content = ""

                for file in selected_files:
                    content = db_handler.get_action_content_by_name(file, "action")
                    if content:
                        merged_content += f"\n### {file} ###\n{content}\n"
                    else:
                        st.warning(f"⚠️ Could not load content for: {file}")
                st.session_state.test_data_action_data = merged_content

        st.markdown("**Enter the additional information or sample data** <span style='color:red;'>*</span>",
                    unsafe_allow_html=True)
        st.session_state.test_data_addition_info= st.text_area("Optional: Provide additional test data", "",key="user_data_textarea")
        if st.button("Generate Functional Test Data"):
            if st.session_state.test_data_action_data:
              constructed_prompt=utils.generate_promot_test_data_generator("test_data",st.session_state.test_data_action_data,st.session_state.test_files_content,st.session_state.test_data_addition_info)
              st.session_state.test_data_llm_response=utils.get_queries_from_ai_updated(constructed_prompt)
              st.success("Test data generated for given input")
            else:
                st.error("Please select action file")
        if st.session_state.test_data_llm_response:
            test_data_file_name = st.text_input("Enter the testdata file Name:")
            if st.button("Save Test Data"):
                if test_data_file_name:
                    utils.save_test_data_into_excel(st.session_state.test_data_llm_response,test_data_file_name,test_data_folder)
                    st.success("Test data generated successfully")

                else:
                    st.error("Please select test data file name")

if st.session_state.checkbox5_state:
    with st.expander("🔎 Locators 🧾 POM File Generator",expanded=st.session_state.open_expander_collection):
        st.title("Locator Generator for Visible Elements")

        # page_url = st.text_input("Enter the URL of the page:")
        selected_app = st.multiselect(
            "Select application type:",
            ["PowerBi", "Web"],
            default=["Web"])
        tags_placeholder = st.empty()
        if "Web" in selected_app:
            # print("xpath_tags",xpath_tag_keys)

            selected_tags = tags_placeholder.multiselect(
                "Select element types to extract:",
                #["input", "button", "a", "select", "textarea", "div", "span","i","li","All"],
                xpath_tag_keys,
                default= st.session_state.selected_tags ,
                key="selected_tags_multiselect"
            )
        else:
            tags_placeholder.empty()  # Hides the tag selection for PowerBi only
            selected_tags = []  # No tags for PowerBi

        st.session_state.selected_app = selected_app
        st.markdown("<a name='top-button'></a>", unsafe_allow_html=True)
        collect_clicked = st.button("Collecting Elements", key="collect_btn")

        if collect_clicked:
            # --- Reset all previous session states before collecting new elements ---
            st.session_state.selected_tags = selected_tags
            handles = st.session_state.driver.window_handles
            if len(handles) > 1:
                st.session_state.driver.switch_to.window(handles[-1])

            for key in ["prompt_response", "selected_xpaths", "prompt_response_page_file", "show_popup", "show_form"]:
                if key in st.session_state:
                    st.session_state[key] = "" if "response" in key else False

            formatted_summary = None
            st.session_state.selected_xpaths = []
            st.session_state.prompt_response = ""
            page_identifier = st.session_state.driver.current_url  # Collect visible elements
            if "PowerBi" in selected_app:
                formatted_summary = utils.get_visible_element_powerBi(st.session_state.driver, page_identifier)
                # get_visible_element_iframe(st.session_state.driver,page_identifier,st.session_state.selected_tags))
            if "Web" in selected_app:
                formatted_summary = utils.get_visible_element_iframe(st.session_state.driver, page_identifier,
                                                                    st.session_state.selected_tags)
                # formatted_summary = utils.get_visible_element(st.session_state.driver, page_identifier,
                #                                                     st.session_state.selected_tags)
            if formatted_summary is None:
                formatted_summary = []
            if formatted_summary:
                if "PowerBi" in selected_app:
                    # prompt = f"Generate multiple XPath expressions for the input and button elements based on the following details. Consider various attributes, hierarchy levels, and text content to create comprehensive XPath variations for each element: {formatted_summary}"
                    st.session_state.prompt_response = utils.get_queries_from_ai("PowerBi", formatted_summary)
                    print("OPen Ai response" + st.session_state.prompt_response)
                if "Web" in selected_app:
                    # prompt = f"Generate multiple XPath expressions for the input and button elements based on the following details. Consider various attributes, hierarchy levels, and text content to create comprehensive XPath variations for each element: {formatted_summary}"
                    st.session_state.prompt_response = utils.get_queries_from_ai("Web", formatted_summary)
                    print("OPen Ai response" + st.session_state.prompt_response)
            else:
                st.info("No elements found in selected tag")
        # Simulate the AI response for demonstration
        # Display the XPath selection UI only after receiving a prompt response
        if st.session_state.prompt_response:
            xpath_dict = utils.filter_duplicate_xpaths(
                utils.selecting_xpath(st.session_state.prompt_response))
            print(xpath_dict)
            st.title("Select XPath Expressions to Add to Excel")
            # Define a persistent placeholder at the top of the expander
            xpath_output_placeholder = st.empty()
            with xpath_output_placeholder.container():
                st.session_state.selected_xpaths = utils.adding_xpath_user_view(xpath_dict)
            page_name = st.text_input("Enter the Page Name:")
            # Show "Add Selected XPaths to Excel" button only after XPaths are displayed
            if st.button("Add Selected XPaths to Excel"):
                if page_name and st.session_state.selected_xpaths:
                    print("going inside add excel")
                    print(st.session_state.selected_xpaths)
                    if st.session_state.selected_xpaths:
                        print("going inside add excel")
                        utils.adding_selected_xapth_excel(page_name)
                        st.session_state.show_popup = True
                        st.session_state.show_form = False  # Reset form visibility
                    # Show popup only if the flag is set
                elif not st.session_state.selected_xpaths:
                    st.error("Select at-least one xpath to add")
                elif not page_name:
                    st.error("Enter the Page name to add the selected xpath")

            if st.session_state.show_popup and not st.session_state.show_form:
                st.write("**Do you want to generate the page file?**")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes"):
                        st.session_state.show_popup = False  # Hide popup
                        st.session_state.show_form = True  # Show form for page file generation

                with col2:
                    if st.button("No"):
                        for _ in range(2):
                            st.session_state.show_popup = False
                            st.session_state.show_form = False
                            st.session_state.prompt_response = ""
                            xpath_output_placeholder = st.empty()
                            #st.write("Page file generation skipped.")
                            st.session_state.xpath_for_new_page_user_info = True
                            st.rerun()
                        st.info(
                            "Page file generation skipped..Please change to the new page in the browser and click 'Collecting Elements' again.")
            # Show popup only if the flag is set
            if st.session_state.show_form:
                st.header("Generating Page File")
                page_name = st.text_input("Enter Page Name (same as xpath details)", value=page_name)
                language = st.selectbox("Select Language", ["Java-Selenium","Java-Playwright","Python-Selenium", "Python-Playwright"])
                Action_data = ""
                if source == "file":
                    Action_data = utils.select_and_read_text_files_xpath("xpath", Action_collection)
                elif source == "database":
                    all_files = db_handler.get_all_action_names()
                    selected_files = st.multiselect("Select saved action files from database for pagefile",
                                                    all_files)

                    if selected_files:
                        merged_content = ""

                        for file in selected_files:
                            content = db_handler.get_action_content_by_name(file, "action")
                            if content:
                                merged_content += f"\n### {file} ###\n{content}\n"
                            else:
                                st.warning(f"⚠️ Could not load content for: {file}")
                        Action_data = merged_content
                # action_prompt = f"""Summarize the following context into a concise and structured format (under 100 lines), preserving key actions, entities, and sequences. The goal is to retain essential meaning for AI understanding, automation, or test case generation. Avoid repetition, and group related items logically. Context: {Action_data} """
                # action_data_processed = utils.get_queries_from_ai_updated(action_prompt)

                if st.button("Generate Page File"):
                    st.session_state.prompt_response_page_file = ""
                    Prompt = utils.generate_pom_from_excel_with_action(language, page_name, language,
                                                                       Action_data)
                    st.session_state.prompt_response_page_file = utils.get_queries_from_ai("Page_File", Prompt)
                    st.subheader("Generated Page Class")
                    if source == "file":
                        utils.create_java_file(page_name, language, st.session_state.prompt_response_page_file)
                        st.success(f"Page file generated for '{page_name}' in '{language}' language.")
                        st.session_state.xpath_for_new_page=True
                    elif source == "database":
                        db_handler.save_pagefile_to_db(page_name, st.session_state.prompt_response_page_file,
                                                       get_update_user(), language)
                        st.success(f"Page file save in database for '{page_name}' in '{language}' language.")
                        st.session_state.xpath_for_new_page = True

                    # --- Add new button to continue for new page ---
        if st.session_state.xpath_for_new_page and st.button("Continue for New Page"):
            for _ in range(2):
                xpath_output_placeholder = st.empty()
                st.session_state.prompt_response_page_file = ""
                st.session_state.prompt_response = ""
                st.session_state.selected_xpaths = []
                st.session_state.show_popup = False
                st.session_state.show_form = False
                st.session_state.xpath_for_new_page = False
                # Clear the previous XPath selection in the UI
                xpath_output_placeholder.empty()
                st.session_state.xpath_for_new_page_user_info=True
                st.rerun()

        if st.session_state.xpath_for_new_page_user_info:
            st.info(
                "Please change to the new page in the browser and click 'Collecting Elements' again.")
            st.session_state.xpath_for_new_page_user_info = False
    if st.session_state.checkbox6_state:
        st.session_state.failed_files = []
        with st.expander("🧾 Test Automation Script Generator"):
            st.title("Automation Script Generator using page file and test cases")
            test_file_name=st.text_input("Enter the test File Name")
            test_file_language = st.selectbox("Select Language for test file",["Java-Selenium","Java-Playwright","Python-Selenium", "Python-Playwright","Desktop & Web[python-Selenium]","UTAM-JavaScript"] )
            if test_file_language != "Desktop & Web[python-Selenium]":
                page_files_content=""
                test_files_content=""
                Action_data=""
                if source == "file":
                    page_files_content = utils.select_and_read_text_files_xpath("page_test", Page_collection)
                    test_files_content = utils.select_and_read_text_files_xpath("testcase_test",Test_case_collection)
                    Action_data = utils.select_and_read_text_files_xpath("recorded action (Optional)", Action_collection)
                elif source == "database":
                    all_page_files = db_handler.get_all_pagefile_names()
                    all_testcase_files=db_handler.get_all_testcasefile_names()
                    selected_page_files = st.multiselect("Select saved page files from database", all_page_files)
                    selected_testcase_files = st.multiselect("Select saved testcase files from database", all_testcase_files)
                    if selected_page_files:
                        merged_page_content = ""

                        for file in selected_page_files:
                            content = db_handler.get_action_content_by_name(file,"page")
                            if content:
                                merged_page_content += f"\n### {file} ###\n{content}\n"
                            else:
                                # st.warning(f"⚠️ Could not load content for: {file}")
                                st.session_state.failed_files.append(file)
                            if st.session_state.failed_files:
                                st.warning("⚠️ Could not load content for the following files:\n- " + "\n- ".join(
                                    st.session_state.failed_files))
                        page_files_content = merged_page_content
                    if selected_testcase_files:
                        merged_testcase_content = ""

                        for file in selected_testcase_files:
                            content = db_handler.get_action_content_by_name(file,"testcase")
                            if content:
                                merged_testcase_content += f"\n### {file} ###\n{content}\n"
                            else:
                                # st.warning(f"⚠️ Could not load content for: {file}")
                                st.session_state.failed_files.append(file)

                        test_files_content = merged_testcase_content
                        if st.session_state.failed_files:
                            st.warning("⚠️ Could not load content for the following files:\n- " + "\n- ".join(
                                st.session_state.failed_files))
                    all_files = db_handler.get_all_action_names()
                    selected_files = st.multiselect("Select saved action files from database for Testscript (optional)", all_files)

                    if selected_files:
                        merged_content = ""

                        for file in selected_files:
                            content = db_handler.get_action_content_by_name(file, "action")
                            if content:
                                merged_content += f"\n### {file} ###\n{content}\n"
                            else:
                                st.warning(f"⚠️ Could not load content for: {file}")
                        Action_data = merged_content
                    # action_prompt = f"""Summarize the following context into a concise and structured format (under 100 lines), preserving key actions, entities, and sequences. The goal is to retain essential meaning for AI understanding, automation, or test case generation. Avoid repetition, and group related items logically. Context: {Action_data} """
                    # action_data_processed = utils.get_queries_from_ai_updated(action_prompt)
                if st.button("Generate_Test_Script", key="gen_script_main"):
                    Lang_lib= "Test-" + test_file_language
                    Prompt = utils.generate_test_script(Lang_lib, test_file_language, page_files_content,test_files_content,Action_data)
                    print("**********Script validator prompt************"+Prompt)
                    test_script_response= utils.get_queries_from_ai_updated(Prompt)
                    # Lang_lib_validate = "Test-validate-" + test_file_language
                    # script_validator_prompt=utils.generate_script_validator(Lang_lib_validate,page_files_content,test_script_response)
                    # test_script_response = utils.get_queries_from_ai_updated(script_validator_prompt)
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
                    Action_data = utils.select_and_read_text_files_xpath("recorded action",
                                                                         Action_collection)
                elif source == "database":
                    all_files = db_handler.get_all_action_names()
                    selected_files = st.multiselect("Select saved action files from database for Testscript (optional)",
                                                    all_files)

                    if selected_files:
                        merged_content = ""

                        for file in selected_files:
                            content = db_handler.get_action_content_by_name(file, "action")
                            if content:
                                merged_content += f"\n### {file} ###\n{content}\n"
                            else:
                                st.warning(f"⚠️ Could not load content for: {file}")
                        Action_data = merged_content
                    # action_prompt = f"""Summarize the following context into a concise and structured format (under 100 lines), preserving key actions, entities, and sequences. The goal is to retain essential meaning for AI understanding, automation, or test case generation. Avoid repetition, and group related items logically. Context: {Action_data} """
                    # action_data_processed = utils.get_queries_from_ai_updated(action_prompt)
                if st.button("Generate_Test_Script", key="gen_script_desktop"):
                    Lang_lib = "Test-" + test_file_language
                    Prompt = utils.generate_test_script_windows_web(Lang_lib,Action_data,test_windows_application_path)
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
                _code_lang = "java" if "java" in _lang.lower() else ("javascript" if "javascript" in _lang.lower() else "python")

                st.subheader("📝 Generated Script")
                st.code(st.session_state.generated_test_script, language=_code_lang)

                with st.expander("✏️ Edit Script (expand to modify before saving)"):
                    edited_script = st.text_area(
                        "Edit the script here:",
                        value=st.session_state.generated_test_script,
                        key=f"script_editor_{ver}",
                        height=500
                    )

                st.subheader("💬 Review Feedback")
                review_details = st.text_area(
                    "Enter specific review details, issues, or requirements (optional):",
                    value="",
                    key=f"script_review_{ver}",
                    height=150,
                    placeholder="e.g., 'TC02 step 3 is missing', 'Add wait for page load after login', ..."
                )
                col_save, col_regen = st.columns(2)
                with col_save:
                    if st.button("💾 Save Generated Script", key="save_script_btn"):
                        final_script = st.session_state.get(f"script_editor_{ver}", st.session_state.generated_test_script)
                        gen_source = st.session_state.script_gen_inputs.get("source", source)
                        if gen_source == "file":
                            utils.create_test_file(Test_file_generator, test_file_name, test_file_language, final_script)
                        elif gen_source == "database":
                            db_handler.save_testfile_to_db(test_file_name, final_script, get_update_user(), test_file_language)
                        st.success("✅ Script saved successfully!")
                        st.session_state.generated_test_script = None
                with col_regen:
                    if st.button("🔄 Regenerate Script", key="regen_script_btn"):
                        current_script = st.session_state.get(f"script_editor_{ver}", st.session_state.generated_test_script)
                        current_review = st.session_state.get(f"script_review_{ver}", "")
                        inputs = st.session_state.script_gen_inputs
                        regen_prompt = utils.generate_code_review_prompt(
                            inputs["test_file_language"],
                            inputs.get("page_files_content", ""),
                            inputs.get("test_files_content", ""),
                            inputs.get("Action_data", ""),
                            current_script,
                            current_review
                        )
                        regenerated_script = utils.get_queries_from_ai_updated(regen_prompt)
                        st.session_state.generated_test_script = regenerated_script
                        st.session_state.script_editor_version = ver + 1
                        st.rerun()

if st.session_state.checkbox7_state:
    with st.expander("⚙️ Source Code 📡 Automation Bridge"):
        st.title("Upload code to Repository")
        if source == "file":
            pytest_files = utils.select_and_read_text_files_xpath("test_file", utils.Test_file_generator)
            pom_files = utils.select_and_read_text_files_xpath("pom_file", utils.Page_file_generator)
        elif source == "database":
            all_page_files = db_handler.get_all_pagefile_names()
            all_test_files = db_handler.get_all_testfile_names()
            selected_page_files = st.multiselect("Select saved page files from database to push", all_page_files)
            selected_test_files = st.multiselect("Select saved testcase files from database to push", all_test_files)
            temp_dir_page=db_handler.prepare_selected_files_for_github(selected_page_files)
            temp_dir_test = db_handler.prepare_selected_files_for_github(selected_test_files)
        repo_pom_name = st.text_input("Enter folder name in repo:", value="test_web/src/pom/pages")
        repo_pytest_name = st.text_input("Enter folder name in repo:", value="test_web/tests/test_cases")

        if st.button("Push to Repo"):

            token = os.getenv("GITLAB_ACCESS_TOKEN")

            if token:
                try:
                    g = Gitlab("https://git.tigeranalytics.com/", private_token=token, ssl_verify=False)
                    g.auth()
                    print("✅ Authentication successful!")
                except Exception as e:
                    print("❌ Auth failed:", e)
            else:
                print("❌ Token not found in environment.")
            repo = g.projects.get(os.getenv("GITLAB_REPO_NAME"))
            print(repo)
            branch = os.getenv("GITLAB_BRANCH_NAME", "main")

            if repo_pom_name and repo_pytest_name:
                if source == "file":
                    # Push all POM files
                    for file_name, content in pom_files.items():
                        pom_dest_path = f"{repo_pom_name.strip('/')}/{file_name}"
                        utils.push_file_to_gitlab(pom_dest_path, content, repo, branch)

                    # Push all pytest files
                    for file_name, content in pytest_files.items():
                        pytest_dest_path = f"{repo_pytest_name.strip('/')}/{file_name}"
                        utils.push_file_to_gitlab(pytest_dest_path, content, repo, branch)
                elif source == "database":
                    # Push all selected page files
                    if temp_dir_page and os.path.isdir(temp_dir_page):
                        for file_name in os.listdir(temp_dir_page):
                            file_path = os.path.join(temp_dir_page, file_name)
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            pom_dest_path = f"{repo_pom_name.strip('/')}/{file_name}"
                            utils.push_file_to_gitlab(pom_dest_path, content, repo, branch)

                    # Push all selected test files
                    if temp_dir_test and os.path.isdir(temp_dir_test):
                        for file_name in os.listdir(temp_dir_test):
                            file_path = os.path.join(temp_dir_test, file_name)
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            pytest_dest_path = f"{repo_pytest_name.strip('/')}/{file_name}"
                            utils.push_file_to_gitlab(pytest_dest_path, content, repo, branch)

                    # Clean up the temp directories
                    shutil.rmtree(temp_dir_page, ignore_errors=True)
                    shutil.rmtree(temp_dir_test, ignore_errors=True)

                    st.success("✅ Selected database files pushed to GitHub and temp files deleted.")
            else:
                st.warning("⚠️ Please enter both folder names in the repo.")


if st.session_state.checkbox8_state:
    if source == "database":
        with st.expander("📥 Download Artifacts"):
            st.title("Download Artifacts from Database")
            file_type = st.selectbox("Select FileType",
                            ["Recorded_Action_file", "Page_file", "Test_file", "Testcase_file"])

            selected_files = []

            if file_type == "Recorded_Action_file":
                files = db_handler.get_all_action_names()
                selected_files = st.multiselect("Select Actions", files)
            elif file_type == "Page_file":
                files = db_handler.get_all_pagefile_names()
                selected_files = st.multiselect("Select Page Files", files)
            elif file_type == "Test_file":
                files = db_handler.get_all_testfile_names()
                selected_files = st.multiselect("Select Test Files", files)
            elif file_type == "Testcase_file":
                files = db_handler.get_all_testcasefile_names()
                selected_files = st.multiselect("Select Testcase Files", files)

            if st.button("📦 Download Files"):
                if selected_files:
                    zip_bytes = db_handler.download_files_from_database(selected_files, file_type)
                    if zip_bytes:
                        st.download_button(
                            label="⬇️ Download ZIP",
                            data=zip_bytes,
                            file_name="artifacts.zip",
                            mime="application/zip"
                        )
                        st.success(f"✅ Prepared {len(selected_files)} files for download.")
                    else:
                        st.warning("⚠️ Could not prepare the ZIP.")
                else:
                    st.warning("⚠️ Please select at least one file.")
if st.session_state.checkbox9_state:
    with st.expander("🚀 Test Execution & Allure Reporting"):
        st.title("Execute Generated Test Scripts and View Allure Reports")

        # List test files
        if source == "file":
            test_files = [f for f in os.listdir(Test_file_generator) if f.endswith('.py')]
            selected_file = st.selectbox("Select Test Script to Execute", test_files, key="test_file_select") if test_files else None
        elif source == "database":
            all_test_files = db_handler.get_all_testfile_names()
            selected_file = st.selectbox("Select Test Script to Execute", all_test_files, key="test_file_select") if all_test_files else None

        if selected_file:
            if st.button("Run Test Script"):
                if source == "file":
                    test_path = os.path.join(Test_file_generator, selected_file)
                elif source == "database":
                    # For database, we need to save the file temporarily or run it differently
                    # Assuming we can get the content and save to temp
                    content = db_handler.get_action_content_by_name(selected_file, "testfile")
                    if content:
                        temp_test_file = os.path.join(current_path, f"temp_{selected_file}.py")
                        with open(temp_test_file, "w") as f:
                            f.write(content)
                        test_path = temp_test_file
                    else:
                        st.error("Could not load test file from database.")
                        test_path = None
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
                        # Clean up temp file if created
                        if source == "database":
                            if 'temp_test_file' in locals():
                                os.remove(temp_test_file)
                    except Exception as e:
                        st.error(f"❌ Error running test: {e}")

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
st.markdown("""    
    ### Contact Us
    - Reach us at [QE Core Team](mailto:sahil.gupta@tigeranalytics.com)
""")


# Create 10 columns
col0, col1, col2, col3, col4, col5, col6, col7,col8,col9= st.columns(10)

with col0:
    st.write("Choose display")
with col1:
    checkbox1 = st.checkbox("(1)", value=st.session_state.checkbox1_state)
    if st.session_state.checkbox1_state != checkbox1:
        st.session_state.checkbox1_state = checkbox1  # Update session state
        st.rerun()
with col2:
    checkbox2 = st.checkbox("(2)", value=st.session_state.checkbox2_state)
    if st.session_state.checkbox2_state != checkbox2:
        st.session_state.checkbox2_state = checkbox2  # Update session state
        st.rerun()
with col3:
    checkbox3 = st.checkbox("(3)", value=st.session_state.checkbox3_state)
    if st.session_state.checkbox3_state != checkbox3:
        st.session_state.checkbox3_state = checkbox3  # Update session state
        st.rerun()
with col4:
    checkbox4 = st.checkbox("(4)", value=st.session_state.checkbox4_state)
    if st.session_state.checkbox4_state != checkbox4:
        st.session_state.checkbox4_state = checkbox4  # Update session state
        st.rerun()
with col5:
    checkbox5 = st.checkbox("(5)", value=st.session_state.checkbox5_state)
    if st.session_state.checkbox5_state != checkbox5:
        st.session_state.checkbox5_state = checkbox5  # Update session state
        st.rerun()
with col6:
    checkbox6 = st.checkbox("(6)", value=st.session_state.checkbox6_state)
    if st.session_state.checkbox6_state != checkbox6:
        st.session_state.checkbox6_state = checkbox6  # Update session state
        st.rerun()
with col7:
    checkbox7= st.checkbox("(7)", value=st.session_state.checkbox7_state)
    if st.session_state.checkbox7_state != checkbox7:
        st.session_state.checkbox7_state = checkbox7  # Update session state
        st.rerun()

with col8:
    checkbox8= st.checkbox("(8)", value=st.session_state.checkbox8_state)
    if st.session_state.checkbox8_state != checkbox8:
        st.session_state.checkbox8_state = checkbox8  # Update session state
        st.rerun()
with col9:
    checkbox9= st.checkbox("(9)", value=st.session_state.checkbox9_state)
    if st.session_state.checkbox9_state != checkbox9:
        st.session_state.checkbox9_state = checkbox9  # Update session state
        st.rerun()

