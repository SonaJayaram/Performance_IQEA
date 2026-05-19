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
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\sona.jayaram\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
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
# page_screenshot_folder = os.path.join(Action_collection, "Sauce_demo")
page_screenshot_folder = os.path.join(Action_collection, "Blaze_demo")
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
if 'injected_windows' not in st.session_state:
    st.session_state.injected_windows= {}
if 'workflow_text_desktop' not in st.session_state:
    st.session_state.workflow_text_desktop = []
if "xpath_for_new_page" not in st.session_state:
    st.session_state.xpath_for_new_page = False
if "xpath_for_new_page_user_info" not in st.session_state:
    st.session_state.xpath_for_new_page_user_info = False

# --- Track expander state only for collection ---
if "open_expander_collection" not in st.session_state:
    st.session_state.open_expander_collection = False
if "recorded_actions_history" not in st.session_state:
    st.session_state.recorded_actions_history = False

# ---------- TMT integration----------
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

st.title(" 🤖 TigerQE AI Platform - Performance Testing")

###desktop
if "desktop_action_name" not in st.session_state:
    st.session_state.desktop_action_name = ""
if "recorder" not in st.session_state:
    st.session_state.recorder = DesktopRecorder()
# 1. Open the browser
page_url = st.text_input("Enter the URL of the page:")
st.session_state.page_url = page_url
if st.button("Open Browser"):
    if page_url:
        chromedriver_path = os.path.join(input_folder, "chromedriver.exe")
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")  # 🔑 prevents Skia/SharedImage GPU errors
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--remote-allow-origins=*")
        chrome_options.add_argument("--disable-dev-shm-usage")
        #chrome_options.binary_location = chromedriver_path
        #service = Service(executable_path=chromedriver_path)
        #service = Service(ChromeDriverManager().install())
        st.session_state.driver = webdriver.Chrome(options=chrome_options)
        #st.session_state.driver = webdriver.Chrome(service=service, options=chrome_options)
        st.session_state.driver.get(page_url)
        st.session_state.driver.maximize_window()
        WebDriverWait(st.session_state.driver, 30).until(utils.is_page_loaded)
        st.success("✅ Browser opened and ready.")

if st.session_state.checkbox5_state:
    with st.expander("🔎 JMX script generator ", expanded=st.session_state.open_expander_collection):
        st.title("JMX using prompt")
        if "generated_jmx" not in st.session_state:
            st.session_state["generated_jmx"] = ""
        st.title("AI-Based JMX Script Generator")

        st.markdown("Enter your prompt for generating a JMeter (.jmx) script.")

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
        """,
        )

        # ---------------- GENERATE BUTTON ----------------
        if st.button("Generate JMX Script"):

            if not user_prompt.strip():
                st.error("Please enter a prompt.")
            else:
                with st.spinner("Generating JMX script using AI..."):

                    # AI Prompt
                    final_prompt = f"""
                    Generate a complete Apache JMeter JMX script based on the following requirement.

                    Requirements:
                    {user_prompt}

                    Instructions:
                    - Generate valid JMX XML structure
                    - Include Thread Group
                    - Include HTTP Requests
                    - Add Assertions wherever applicable
                    - Add Listeners
                    - Ensure the output is pure XML JMX content
                    - Do not include explanations
                    """

                    # Call AI utility
                    response = utils.get_output_from_ai( final_prompt)

                    st.session_state.generated_jmx = response

        # ---------------- DISPLAY GENERATED JMX ----------------
        if st.session_state.generated_jmx:
            st.subheader("Generated JMX Script")

            st.text_area(
                "JMX Output",
                value=st.session_state.generated_jmx,
                height=500
            )

            # ---------------- DOWNLOAD BUTTON ----------------
            st.download_button(
                label="Download JMX File",
                data=st.session_state.generated_jmx,
                file_name="generated_test_plan.jmx",
                mime="application/xml"
            )

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
                    handle=st.session_state.driver.current_window_handle
                    st.session_state.driver.execute_script(action_utils.injection_script_updated_fixed())
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
                st.session_state.recording_started = False

                # Signal all threads to stop
                st.session_state.stop_monitor["stop"] = True

                # Join all monitor threads
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
if st.session_state.checkbox3_state:
    with (st.expander("🧮 Performance Test Script Generator")):

        st.title("Performance Test Script Generator")

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
        if st.button("Generate Performance Test Cases"):
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
                    image_data_processed = utils.get_queries_from_ai_updated(image_prompt)
                    if not Action_data:
                        Action_data = None
                    if model_type == "azureopenai":
                        print("Model Type is AzureOpenAi")
                        constructedprompt = utils.generate_pom_from_excel_testcases("performance_testcase_generation", navigation,
                                                                              image_data_processed, Action_data,
                                                                               prompt)
                    else:
                        print("Model Type is pepgenx")
                        constructedprompt = utils.generate_pom_from_excel_testcases("Test_case_generation_gemini", navigation,
                                                                                    image_data_processed, Action_data,
                                                                                    prompt)
                    print("******final prompt *******")
                    # count_prompt=utils.generate_pom_from_excel_testcases("Testcase_coverage_plan_recorded_details_flow", navigation,
                    #                                                           image_data_processed, Action_data,
                    #                                                            prompt)
                    # coverage_counts=utils.estimate_testcase_coverage(count_prompt)
                    # st.info(coverage_counts)
                    # # Safely get RecommendedTotal, fallback to 50 if key missing
                    # target_count = coverage_counts.get("RecommendedTotal", 50)
                    #
                    # print(f"✅ Recommended total test cases for generation: {target_count}")
                    #st.session_state.testcase_response = utils.generate_testcases_with_retries(constructedprompt)
                    st.session_state.testcase_response = utils.get_queries_from_ai_updated(constructedprompt)
                    #st.code(st.session_state.testcase_response)
                    # utils.parse_and_display_testcases_categorywise(st.session_state.testcase_response)
                    st.write(" ")

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

        if st.session_state.testcase_response:
            st.session_state.save_testcases = True
        if st.session_state.save_testcases and st.button("💾 Save test cases"):

            utils.covert_response_to_testcases_single_file(st.session_state.testcase_response, Test_case_collection)
            #utils.covert_response_to_testcases(st.session_state.testcase_response, Test_case_collection)
            st.session_state.jmx_path=utils.save_response_to_jmetertestcase(st.session_state.testcase_response, Test_case_collection)
            st.session_state.testcases_saved = True
            st.session_state.show_popup = True
            st.session_state.show_form = False

        if st.session_state.get("testcases_saved"):
            if option == "Documents" and source_type == "Azure Board":
                if st.button("📤 Export test cases to azure Board"):
                    try:
                        sub_work_item=tmt_utils.create_test_case(st.session_state.azure_workitem_id)
                        tmt_utils.upload_attachment_to_testcase(sub_work_item,st.session_state.excel_path)
                    except Exception as e:
                        st.error("Invalid Work Item")
                    st.success(f"✅ Test cases were successfully exported!\n\n📄 Work Item ID: **{sub_work_item}**")
                    st.session_state.save_testcases = False
            elif option == "Documents" and source_type == "Files":
                if st.session_state.show_popup and not st.session_state.show_form:
                    st.write("**Do you want to export the generated testcases?**")

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
                                # st.write("Page file generation skipped.")
                                st.session_state.xpath_for_new_page_user_info = True
                                st.rerun()
                            st.info(
                                "Test Case export skipped.")
                # Show popup only if the flag is set
                if st.session_state.show_form:
                    st.info("Enter Jira Work Item ID (numeric)")
                    workitem = st.text_input("jira Work Item ID", value=st.session_state.azure_workitem_id,
                                             key="azure_workitem_text")
                    st.session_state.azure_workitem_id = workitem.strip()
                    if workitem and not workitem.isdigit():
                        st.warning("Work Item ID typically numeric — ensure it's correct.")
                    if st.button("📤 Export test cases to azure Board"):

                        if st.session_state.azure_workitem_id:
                            try:
                                exists, message = tmt_utils.validate_work_item_exists(
                                    st.session_state.azure_workitem_id)
                                if exists:
                                    child_id = tmt_utils.create_test_case(st.session_state.azure_workitem_id)
                                    tmt_utils.upload_attachment_to_testcase(child_id, st.session_state.excel_path)
                                    st.success(f"✅ Test cases were successfully exported!\n\n📄 Work Item ID: **{child_id}**")
                                else:
                                    st.error(f"{message} — Please enter a valid Work Item.")
                                    st.stop()

                            except Exception as e:
                                st.error("Invalid Work Item")
                        else:
                            try:
                                child_id=tmt_utils.create_direct_test_case()
                                tmt_utils.upload_attachment_to_testcase(child_id, st.session_state.excel_path)
                                st.success(f"✅ Test cases were successfully exported!\n\n📄 Work Item ID: **{child_id}**")
                            except Exception as e:
                                st.error("Invalid Work Item")

            elif option == "Recorded_Details":
                if st.session_state.show_popup and not st.session_state.show_form:
                    st.write("**Do you want to export the generated testcases?**")

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
                                # st.write("Page file generation skipped.")
                                st.session_state.xpath_for_new_page_user_info = True
                                st.rerun()
                            st.info("Test Case export skipped.")
                # Show popup only if the flag is set
                if st.session_state.show_form:
                    st.info("Enter jira Work Item ID (numeric)")
                    workitem = st.text_input("jira Work Item ID", value=st.session_state.azure_workitem_id,
                                             key="azure_workitem_text")
                    st.session_state.azure_workitem_id = workitem.strip()
                    if workitem and not workitem.isdigit():
                        st.warning("Work Item ID typically numeric — ensure it's correct.")
                    if st.button("📤 Export test cases to azure Board"):

                        if st.session_state.azure_workitem_id:
                            try:
                                exists, message = tmt_utils.validate_work_item_exists(
                                    st.session_state.azure_workitem_id)
                                if exists:
                                    child_id = tmt_utils.create_test_case(st.session_state.azure_workitem_id)
                                    tmt_utils.upload_attachment_to_testcase(child_id, st.session_state.excel_path)
                                    st.success(f"✅ Test cases were successfully exported!\n\n📄 Work Item ID: **{child_id}**")
                                else:
                                    st.error(f"{message} — Please enter a valid Work Item.")
                                    st.stop()

                            except Exception as e:
                                st.error("Invalid Work Item")
                        else:

                            try:
                                child_id=tmt_utils.create_direct_test_case()
                                tmt_utils.upload_attachment_to_testcase(child_id, st.session_state.excel_path)
                                st.success(f"✅ Test cases were successfully exported!\n\n📄 Work Item ID: **{child_id}**")
                            except Exception as e:
                                st.error("Invalid Work Item")

if st.session_state.checkbox9_state:
    with st.expander("🚀 Test Execution & Html Report"):
        st.title("Execute Generated Test Scripts and View Html Reports")

        # List test files
        if source == "file":
            test_files = [f for f in os.listdir(Test_case_collection) if f.endswith('.jmx')]
            selected_file = st.selectbox("Select Test Script to Execute", test_files, key="test_file_select") if test_files else None
        elif source == "database":
            all_test_files = db_handler.get_all_testfile_names()
            selected_file = st.selectbox("Select Test Script to Execute", all_test_files, key="test_file_select") if all_test_files else None

        if selected_file:
            import subprocess
            import os
            import streamlit as st

            JMETER_PATH = r"D:\Practice\apache-jmeter-5.5\apache-jmeter-5.5\apache-jmeter-5.5\bin\jmeter.bat"  # 🔴 update this path

            if st.button("Run Test Script"):

                if source == "file":
                    test_path = os.path.join(Test_case_collection, selected_file)
                    print("#### test_path ### ", test_path)

                elif source == "database":
                    content = db_handler.get_action_content_by_name(selected_file, "testfile")
                    if content:
                        temp_test_file = os.path.join(current_path, f"{selected_file}.jmx")
                        with open(temp_test_file, "w", encoding="utf-8") as f:
                            f.write(content)
                        test_path = temp_test_file
                    else:
                        st.error("Could not load test file from database.")
                        test_path = None

                if test_path:
                    result_file = os.path.join(current_path, "results.jtl")
                    report_folder = os.path.join(current_path, "jmeter-report")

                    command = [
                        JMETER_PATH,
                        "-n",
                        "-t", test_path,
                        "-l", result_file,
                        "-e",
                        "-o", report_folder,
                        "-Jsummariser.name=summary"  # ✅ live progress logs
                    ]

                    try:
                        st.write("🚀 Starting JMeter Test...")

                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            cwd=current_path
                        )

                        log_placeholder = st.empty()
                        status_placeholder = st.empty()

                        logs = ""

                        import time

                        while True:
                            line = process.stdout.readline()

                            # 🔹 If process ended
                            if not line and process.poll() is not None:
                                break

                            # 🔹 Stream logs
                            if line:
                                logs += line
                                log_placeholder.text_area("Execution Logs", logs, height=250)

                                # ✅ Detect active execution
                                if "summary +" in line:
                                    status_placeholder.success("🟢 JMeter is RUNNING (load in progress)")

                                elif "Creating summariser" in line or "Starting the test" in line:
                                    status_placeholder.info("🟡 JMeter is STARTING...")

                            # 🔹 Extra safety: check result file growth
                            if os.path.exists(result_file):
                                size1 = os.path.getsize(result_file)
                                time.sleep(1)
                                size2 = os.path.getsize(result_file)

                                if size2 > size1:
                                    status_placeholder.success("📈 Test is actively writing results → RUNNING")

                        return_code = process.poll()

                        # ✅ Final status
                        if return_code == 0:
                            st.success("✅ JMeter test completed successfully")
                        else:
                            st.error("❌ JMeter execution failed")

                        # Save logs
                        st.session_state.test_execution_status = logs

                        # Cleanup temp file
                        if source == "database" and os.path.exists(test_path):
                            os.remove(test_path)

                    except Exception as e:
                        st.error(f"❌ Error running JMeter: {e}")

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

