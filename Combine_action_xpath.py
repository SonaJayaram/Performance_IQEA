#from github import Github
import streamlit as st
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
import os
import threading
import time
import Utilities_Xpath_Latest as utils
import utils_action as action_utils
from PIL import Image
from Utilities import *
import pytesseract
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
# Setup output folder
current_path = os.getcwd()
input_folder = os.path.join(current_path, "Input")
output_folder = os.path.join(current_path, "output")
Action_collection = os.path.join(output_folder, "Action_collection")
Page_collection = os.path.join(output_folder, "page_file_generator")
Test_case_collection = os.path.join(output_folder, "Test_Cases_collection")
feature_file_collection = os.path.join(output_folder, "Feature_file_generator")
os.makedirs(Page_collection, exist_ok=True)
os.makedirs(Test_case_collection, exist_ok=True)
os.makedirs(Action_collection, exist_ok=True)
os.makedirs(feature_file_collection, exist_ok=True)
page_screenshot_folder = os.path.join(Action_collection, "page_screenshot")
os.makedirs(page_screenshot_folder, exist_ok=True)

st.set_page_config(
    page_title="TigerQE One Stop AI Solution",
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
        st.session_state.selected_tags = []
if 'selected_app' not in st.session_state:
    st.session_state.selected_app = []
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
if "xpath_collection" not in st.session_state:
    st.session_state.xpath_collection= {}
st.title(" 🤖 TigerQE 'One-Stop' AI Solution")
# 1. Open the browser
page_url = st.text_input("Enter the URL of the page:")
st.session_state.page_url = page_url
if st.button("Open Browser"):
    if page_url:
        chrome_options = Options()
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        st.session_state.driver = webdriver.Chrome(options=chrome_options)
        st.session_state.driver.get(page_url)
        st.session_state.driver.maximize_window()
        WebDriverWait(st.session_state.driver, 30).until(utils.is_page_loaded)
        st.success("✅ Browser opened and ready.")

# Display sections based on checkboxes
if st.session_state.checkbox1_state:
    current_url = ""
    with st.expander("🔴 User Workflow Recorder"):
        xpath_collection_global = {}
        # 2. Start Recording
        st.subheader("Record User Actions & Capture Screenshots of User Navigation")
        selected_app = st.multiselect(
            "Select application type:",
            ["PowerBi", "Web"],
            default=["Web"])
        tags_placeholder = st.empty()
        if "Web" in selected_app:
            selected_tags = tags_placeholder.multiselect(
                "Select element types to extract:",
                ["input", "button", "a", "select", "textarea", "div", "span", "All"],
                default=["input", "button"]
            )
        else:
            tags_placeholder.empty()  # Hides the tag selection for PowerBi only
            selected_tags = []  # No tags for PowerBi
        st.session_state.selected_tags = selected_tags
        st.session_state.selected_app = selected_app
        if not st.session_state.recording_started and st.button("🎥 Start Recording"):
            if st.session_state.driver:
                driver=st.session_state.driver
                st.session_state.actions = []
                st.session_state.selected_xpaths = []
                              # Reset previous actions
                action_utils.start_recording(st.session_state.driver)
                st.session_state.recording_started = True
                st.success("Recording started. Please interact with the browser.")

                # Prepare collector thread flag
                st.session_state.stop_monitor = {"stop": False}
                # XPath extraction (based on app type)
                if "PowerBi" in st.session_state.selected_app:
                    first_page_elements = utils.get_visible_element_powerBi(driver, current_url)
                else:
                    first_page_elements = utils.get_visible_element_iframe(driver, current_url,
                                                                st.session_state.selected_tags)

                # AI prompt and processing
                print("first_page_elements")
                print(first_page_elements)
                if first_page_elements:
                    current_url = driver.current_url
                    xpath_collection_global[current_url] = {
                        "collected_elements": first_page_elements,
                    }
                print("xpath_collection")
                st.session_state.xpath_collection=xpath_collection_global
                print(st.session_state.xpath_collection)
                # Start monitoring thread to collect screenshots + XPaths

                def monitor_combined(driver, folder, stop_flag,selected_app, selected_tags):
                    previous_url = driver.current_url
                    while not stop_flag["stop"]:
                        time.sleep(1)
                        current_url = driver.current_url
                        if current_url != previous_url:
                            previous_url = current_url
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            screenshot_path = os.path.join(folder, f"{timestamp}.png")
                            driver.save_screenshot(screenshot_path)
                            st.info(f"📸 Screenshot captured: {screenshot_path}")

                            # XPath extraction (based on app type)
                            if "PowerBi" in selected_app:
                                elements = utils.get_visible_element_powerBi(driver, current_url)
                            else:
                                elements = utils.get_visible_element_iframe(driver, current_url,
                                                                        selected_tags)
                            print("elements")
                            print(elements)
                            # AI prompt and processing
                            if elements:
                                xpath_collection_global[current_url] = {
                                    "collected_elements": elements,
                                }
                            print("xpath_collection_new_page")
                            st.session_state.xpath_collection=xpath_collection_global
                            print(st.session_state.xpath_collection)


                    st.success("✅ Stopped monitoring page transitions.")
                st.session_state.monitor_thread = threading.Thread(
                    target=monitor_combined,
                    args=(st.session_state.driver, page_screenshot_folder, st.session_state.stop_monitor,st.session_state.selected_app,st.session_state.selected_tags),
                    daemon=True
                )
                st.session_state.monitor_thread.start()

        if st.session_state.recording_started and st.button("🛑 Stop Recording"):
            st.session_state.actions = action_utils.get_recorded_actions(st.session_state.driver)
            st.session_state.recording_started = False
            st.session_state.stop_monitor["stop"] = True
            if st.session_state.monitor_thread:
                st.session_state.monitor_thread.join()

            st.success(f"✅ Recording stopped. {len(st.session_state.actions)} actions captured.")

        if st.session_state.actions:
            page_name = st.text_input("Enter Page Name for Saving:")
            if st.button("💾 Save Actions & XPaths"):
                # Save actions
                workflow_text = action_utils.generate_workflow(st.session_state.actions)
                action_file = os.path.join(Action_collection, f"{page_name}_actions.txt")
                with open(action_file, "w") as f:
                    f.write("\n".join(workflow_text))
                st.success(f"🎯 Actions saved: {action_file}")

                # Save XPath collection (all pages visited during recording)
                #for url, data in st.session_state.xpath_collection.items():
                #elements_collected = data["collected_elements"]
                raw_prompt = utils.get_queries_from_ai("Actionxpath", st.session_state.xpath_collection)
                xpath_dict = utils.filter_duplicate_xpaths(utils.selecting_xpath(raw_prompt))
                st.session_state.selected_xpath=utils.adding_xapth_user_view(xpath_dict)
        if st.session_state.selected_xpaths :
            if st.button("Add Selected XPaths to Excel"):
                print("going inside add excel")
                print(st.session_state.selected_xpaths)
                utils.adding_selected_xapth_excel(page_name)
                st.success("🧾 XPath data saved for all visited pages.")


# Create 6 columns
col0, col1, col2, col3, col4, col5, col6 = st.columns(7)

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
