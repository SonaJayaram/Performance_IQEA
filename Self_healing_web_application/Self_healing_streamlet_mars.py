import os
import re
import docx2txt
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from src.mcp_use_client import *
import json
import asyncio
import os
import subprocess
import difflib
import pandas as pd
import os
from src.mcp_use_client import start_mcp_client, execute_mcp_use, close_mcp_client
import Utils.Self_healing_utilities as healing_utils
import Utils.self_healing_framework_utilities as healing_framework_utils
import streamlit as st
import Utils.utils_actions as action_utils
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import Utils.self_healing_framework_utilities as utils
import threading
from config.config_reader import framework_source, git_details, get_source
import Utils.Self_healing_git_utilities as healing_git_utils
st.set_page_config(
    page_title="TigerQE Web Migartion-Comparetor",
     page_icon="🤖🛠️",
    layout="centered"
)
# Session state setup
if "page_url" not in st.session_state:
    st.session_state.page_url=None
if "Action_file_Location" not in st.session_state:
 st.session_state.Action_file_Location=None
if "Git_pages_Location" not in st.session_state:
 st.session_state.Git_pages_Location=None
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
if "Self_healing" not in st.session_state:
    st.session_state.Self_healing = False
if 'actions' not in st.session_state:
    st.session_state.actions = []
if 'Git_Repo' not in st.session_state:
    st.session_state.Git_Repo= None
if 'Git_branch_name'not in st.session_state:
    st.session_state.Git_branch_name= None
if 'self_healing_response'not in st.session_state:
    st.session_state.self_healing_response= []
st.set_page_config(
    page_title="TigerQE Web Migartion-Comparator",
     page_icon="🧭🛠️",
    layout="centered"
)    
st.title("🧭🛠️ TigerQE Web Migartion-Comparator(AI)")
st.markdown("**Enter action file location or Record action workflow to capture the page navigation using User Workflow Recorder** <span style='color:red;'>*</span>", unsafe_allow_html=True)
Action_file_Location = st.text_input(
    "Enter the action file location", 
    value=st.session_state.Action_file_Location or ""
)
# Only update session state if user types something new
if Action_file_Location:
    st.session_state.Action_file_Location = Action_file_Location
st.markdown("<span style='color:black;'><strong>Or</strong></span>",unsafe_allow_html=True)
# 1. Open the browser
with st.expander("🔴 User Workflow Recorder"):
# 2. Start Recording
    st.subheader("Record User Actions & Capture Screenshots of User Navigation")

    page_url = st.text_input("Enter the URL of the page:")
    st.session_state.page_url = page_url
    if st.button("Open Browser"):
        if page_url:
            #chromedriver_path = os.path.join(input_folder, "chromedriver.exe")
            chrome_options = Options()
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            #chrome_options.binary_location = chromedriver_path
            #service = Service(executable_path=chromedriver_path)
            #service = Service(ChromeDriverManager().install())
            st.session_state.driver = webdriver.Chrome(options=chrome_options)
            #st.session_state.driver = webdriver.Chrome(service=service, options=chrome_options)
            st.session_state.driver.get(page_url)
            st.session_state.driver.maximize_window()
            WebDriverWait(st.session_state.driver, 30).until(action_utils.is_page_loaded)
            st.success("✅ Browser opened and ready.")

    if not st.session_state.recording_started and st.button("🎥 Start Recording"):
        if st.session_state.driver:
            st.session_state.actions = [] # reset if previously recorded
            action_utils.start_recording(st.session_state.driver)
            st.session_state.recording_started = True

            # Start thread to monitor URL and take screenshots
            st.session_state.stop_monitor = {"stop": False}
            st.session_state.monitor_thread = threading.Thread(
                target=action_utils.monitor_url_changes_for_each_nav,
                args=(st.session_state.driver, st.session_state.stop_monitor),
                daemon=True
            )
            st.session_state.monitor_thread.start()
            st.success("Recording started. Please interact in the browser.")

    # 3. Stop Recording
    if st.session_state.recording_started and st.button("🛑 Stop Recording"):
        st.session_state.actions = action_utils.get_recorded_actions(st.session_state.driver)
        st.session_state.recording_started = False
        #st.session_state.actions = actions
        # Stop the monitoring thread
        st.session_state.stop_monitor["stop"] = True
        if st.session_state.monitor_thread:
            st.session_state.monitor_thread.join()
        st.success(f"Recording stopped. performed actions are captured.")
        actions=[]

    # 4. Show and Save Actions
    if st.session_state.actions:
        page_name = st.text_input("Enter Page Name for Saving the Workflow:")
        if st.button("💾 Save Workflow"):
            workflow_text = action_utils.generate_workflow(st.session_state.actions)
            if page_name:
                filename = os.path.join(healing_utils.Action_collection, f"{page_name}_actions.txt")
                with open(filename, "w") as f:
                    f.write("\n".join(workflow_text))  # ✅ FIXED
                st.success(f"✅ Workflow saved: {filename}")
                st.session_state.Action_file_Location=filename
                st.download_button("⬇ Download Workflow", data="\n".join(workflow_text),
                                file_name=f"{page_name}_actions.txt")
                st.session_state.actions = []  # clear after save
                st.session_state.show_popup = True
                st.session_state.show_form = False 
                st.session_state.Self_healing = True # Reset form visibility
st.markdown("**Enter New Url**<span style='color:red;'><strong>*</strong></span>",unsafe_allow_html=True)
Git_pages_Location = st.text_input(
    "Enter the Migarated URl", 
    value=st.session_state.Git_pages_Location or ""
)

if Git_pages_Location:
    st.session_state.Git_pages_Location = Git_pages_Location


### capture xpath from framework####
source=get_source()
xpath_file_path,page_folder_path,workflow_doc_path,feature_file_path=framework_source()
git_file_path,git_repo_url,git_branch_name=git_details()
excel_path=os.path.join(healing_utils.output_xpath_validate, "validated_xpath.xlsx")
page_folder=page_folder_path

#========== 🔽 EXECUTION ==========##
if st.button("Execute the Script on Current UI"):
    print("action files\n",st.session_state.Action_file_Location)
    print(st.session_state.Git_pages_Location)
    if all(
    key in st.session_state and st.session_state[key]
    for key in ["Action_file_Location", "Git_pages_Location"]
    ):
        # if source=="local":
        #     healing_framework_utils.generate_xpath_doc(xpath_file_path, st.session_state.Git_pages_Location)
        # else:
        #     healing_git_utils.generate_xpath_doc(
        #         git_repo_url=git_repo_url,
        #         git_branch_name=git_branch_name,
        #         git_page_folder=st.session_state.Git_pages_Location
        #     )
        workflow_content = healing_framework_utils.read_workflow_document(st.session_state.Action_file_Location)
        # Generate feature file from workflow (whole flow as one)
        feature_content = healing_framework_utils.workflow_feature_file(workflow_content)
        feature_file_path=healing_framework_utils.write_feature_file("full_workflow", feature_content)


        #####MCP - Rweady feature , generate JS file
        st.write(f"✅ MCP Server Started scaning the navigation flows....")
        asyncio.run(healing_utils.main(feature_file_path))
        ##### Subprocess to run genearted JS file to get DOM#############
        st.write(f"✅ MCP Server Started naviagted to each and every page to collect the current DOM....")
        subprocess.run(['node', healing_utils.SCRIPT_PATH_execution], check=True)
        print(f"✅ Page wise dom file generated. Output saved to: {healing_utils.dom_file_path}")
        st.write(f"✅ Page wise dom file generated. Output saved to: {healing_utils.dom_file_path}")
if st.button("Execute the Script on migrated UI"):
    print("action files\n",st.session_state.Action_file_Location)
    print(st.session_state.Git_pages_Location)
    if all(
    key in st.session_state and st.session_state[key]
    for key in ["Action_file_Location", "Git_pages_Location"]
    ):
        # if source=="local":
        #     healing_framework_utils.generate_xpath_doc(xpath_file_path, st.session_state.Git_pages_Location)
        # else:
        #     healing_git_utils.generate_xpath_doc(
        #         git_repo_url=git_repo_url,
        #         git_branch_name=git_branch_name,
        #         git_page_folder=st.session_state.Git_pages_Location
        #     )
        workflow_content = healing_framework_utils.read_workflow_document(st.session_state.Action_file_Location)
        # Generate feature file from workflow (whole flow as one)
        feature_content = healing_framework_utils.workflow_feature_file(workflow_content)
        feature_file_path=healing_framework_utils.write_feature_file("full_workflow", feature_content)


        #####MCP - Rweady feature , generate JS file
        st.write(f"✅ MCP Server Started scaning the navigation flows....")
        asyncio.run(healing_utils.main(feature_file_path))
        ##### Subprocess to run genearted JS file to get DOM#############
        st.write(f"✅ MCP Server Started naviagted to each and every page to collect the current DOM....")
        subprocess.run(['node', healing_utils.SCRIPT_PATH_execution], check=True)
        print(f"✅ Page wise dom file generated. Output saved to: {healing_utils.dom_file_path}")
        st.write(f"✅ Page wise dom file generated. Output saved to: {healing_utils.dom_file_path}")
        #### Process Xpath details and page wise dom and validate the xpath #######
        #xpath_file_path=os.path.join(healing_utils.output_generate_xpath, "xpath_details copy.json")
        #xpath_file_path =r"D:\Self_healing_web_application\generated_xpath_details\xpath_details.json"
    #     dom_file_path=os.path.join(healing_utils.output_dom, "all_page_dom_details.json")
    #     #dom_file_path =r"D:\Self_healing_web_application\output\sauce_demo\output\sauce_demo\all_page_dom_details.json"
    #     with open(xpath_file_path, 'r', encoding='utf-8') as f:
    #         xpath_content = f.read()

    #     xpath_content_all=healing_utils.read_json_file(healing_utils.xpath_file_path)
    #     dom_content_all=healing_utils.read_json_file(healing_utils.dom_file_path)
    #     xpath_content_dict = healing_utils.normalize_content(xpath_content_all, details_key="xpath_details")
    #     dom_content_dict = healing_utils.normalize_content(dom_content_all, details_key="dom_details")

    #     print("DEBUG - XPATH dict keys:", xpath_content_dict.keys())
    #     print("DEBUG - DOM dict keys:", dom_content_dict.keys())
    #     #page_mapping = match_xpath_and_dom(xpath_content_all, dom_content_all)
    #     # response =[]
    #     # # Initialize progress bar
    #     # progress_bar = st.progress(0)
    #     # progress_text = st.empty()
    #     # for xpath_page, xpath_details in xpath_content_dict.items():
    #     #     found_match = False
    #     #     for dom_page, dom_details in dom_content_dict.items():
    #     #     # Partial match check
    #     #         if healing_utils.has_partial_word_match(xpath_page, dom_page):
    #     #             response.append(healing_utils.compare_xpathdetails_dom(xpath_details, dom_details))
    #     #             found_match = True
    #     #             break   # stop once match is found

    #     #     if not found_match:
    #     #         print(f"No DOM match found for {xpath_page}")
    #     # st.session_state.self_healing_response=response
    #     # Initialize progress bar
    #     total_pages = len(xpath_content_dict)
    #     progress_bar = st.progress(0)
    #     progress_text = st.empty()
    #     response = []

    #     for i, (xpath_page, xpath_details) in enumerate(xpath_content_dict.items(), start=1):
    #         found_match = False
    #         for dom_page, dom_details in dom_content_dict.items():
    #             # Partial match check
    #             if healing_utils.has_partial_word_match(xpath_page, dom_page):
    #                 response.append(healing_utils.compare_xpathdetails_dom(xpath_details, dom_details))
    #                 found_match = True
    #                 break   # stop once match is found

    #         if not found_match:
    #             print(f"No DOM match found for {xpath_page}")

    #         # Update progress bar
    #         progress = i / total_pages
    #         progress_bar.progress(progress)
    #         progress_text.text(f"Processing page {i}/{total_pages}: {xpath_page}")
    #     st.success("✅ Self-healing comparison completed!")
    #     #### Saving response into excel######
    #     healing_utils.save_ai_response_to_excel(response)
    #     excel_path=os.path.join(healing_utils.output_xpath_validate, "validated_xpath.xlsx")

    #     if source=="local":
    #         healing_utils.replace_invalid_xpaths(excel_path, target_file=None,page_folder=page_folder)
    #     else:    
    #         healing_git_utils.replace_invalid_xpaths(
    #             excel_path=excel_path,
    #             git_repo_url=git_repo_url,
    #             git_branch_name=git_branch_name,
    #             git_file_path=st.session_state.Git_pages_Location
    #         )
    # else:
    #     st.error("Flle above mandatory details")    
    # ### updatre the Alternative xpath in source file #####
    # #excel_path=r"D:\Self_healing_web_application\output\validated_xpath\validated_xpath.xlsx"

# Footer of webpage
st.divider()
st.markdown("""    
    ### Contact Us
    - Reach us at [QE Core Team](mailto:sahil.gupta@tigeranalytics.com)
""")