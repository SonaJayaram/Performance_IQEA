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
source = get_source()
model_type= get_model()
xpath_tag_keys= get_xpath_key()

# Setup output folder
current_path = os.getcwd()
input_folder = os.path.join(current_path, "Input")
output_folder = os.path.join(current_path, "output")
Action_collection = os.path.join(output_folder, "Action_collection")
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
if 'injected_windows' not in st.session_state:
    st.session_state.injected_windows= {}

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
st.title(" 🤖 TigerQE AI Platform - iQEA (Intelligent QE Assistant)")


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

# Display sections based on checkboxes
if st.session_state.checkbox1_state:
    with st.expander("🔴 User Workflow Recorder"):
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
                    image_data_processed = utils.get_queries_from_ai_updated(image_prompt)
                    print(image_data_processed)
                    if not Action_data:
                        Action_data = None
                    if model_type == "azureopenai":
                        print("Model Type is AzureOpenAi")
                        constructedprompt = utils.generate_pom_from_excel_testcases("Test_case_generation", navigation,
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
                    st.session_state.testcase_response = utils.generate_testcases_with_dynamic_stop(constructedprompt,25,1)
                    #st.code(st.session_state.testcase_response)
                    utils.parse_and_display_testcases_categorywise(st.session_state.testcase_response)
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
            st.session_state.excel_path=utils.covert_response_to_testcases_single_sheet(st.session_state.testcase_response, Test_case_collection)
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
            print("xpath_tags",xpath_tag_keys)

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
            test_file_language = st.selectbox("Select Language for test file",["Java-Selenium","Java-Playwright","Python-Selenium", "Python-Playwright"] )
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
            if st.button("Generate_Test_Script"):
                Lang_lib= "Test-" + test_file_language
                Prompt = utils.generate_test_script(Lang_lib, test_file_language, page_files_content,test_files_content,Action_data)
                test_script_response= utils.get_queries_from_ai_updated(Prompt)
                #st.write(test_script_response)
                Lang_lib_validate = "Test-validate-" + test_file_language
                script_validator_prompt=utils.generate_script_validator(Lang_lib_validate,page_files_content,test_script_response)
                #
                test_script_response = utils.get_queries_from_ai_updated(script_validator_prompt)
                # second_level_script_validation=utils.generate_script_validation_prompt("Script_validation_common",page_files_content,test_script_response,Lang_lib)
                # print("second_level_script_validation",second_level_script_validation)
                # final_test_page_script=utils.get_queries_from_ai_updated(second_level_script_validation)
                # print("final_test_page_script", final_test_page_script)
                # utils.update_page_files_from_json(final_test_page_script,Page_collection)
                # test_script_response=utils.extract_test_script_from_json(final_test_page_script)
                # print("validated_test_script", test_script_response)
                if source == "file":
                    utils.create_test_file(Test_file_generator,test_file_name, test_file_language, test_script_response)
                elif source == "database":
                    db_handler.save_testfile_to_db(test_file_name,test_script_response,get_update_user(),test_file_language)
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
# Footer of webpage
st.divider()
st.markdown("""    
    ### Contact Us
    - Reach us at [QE Core Team](mailto:sahil.gupta@tigeranalytics.com)
""")


# Create 10 columns
col0, col1, col2, col3, col4, col5, col6, col7,col8= st.columns(9)

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


