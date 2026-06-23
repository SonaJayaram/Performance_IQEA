import os
from typing import Union, IO
import yaml
import PyPDF2
import random
import utilities.utils_action as action_utils
import time
import string
import json
import ast
import re
import pandas
from io import StringIO
from langchain_core.messages import HumanMessage
from selenium import webdriver
from selenium.common import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import streamlit as st
from langchain_openai import AzureChatOpenAI
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.wait import WebDriverWait
import hashlib
from webdriver_manager.chrome import ChromeDriverManager
from uuid import uuid4
from dotenv import load_dotenv
import os

load_dotenv()
current_path = os.getcwd()
output_folder = os.path.join(current_path, "output")
xpath_generator_folder = os.path.join(output_folder, "xpath_generator")
Page_file_generator = os.path.join(output_folder, "page_file_generator")
Test_file_generator = os.path.join(output_folder, "test_file_generator")
xpath_file = os.path.join(xpath_generator_folder, "xpath_details.xlsx")
os.makedirs(xpath_generator_folder, exist_ok=True)
os.makedirs(Page_file_generator, exist_ok=True)
os.makedirs(Test_file_generator, exist_ok=True)


# Check if the Excel file exists
if not os.path.exists(xpath_file):
    # Just create an empty Excel file (without headers)
    with pd.ExcelWriter(xpath_file) as writer:
        pd.DataFrame().to_excel(writer, index=False)
    print(f"Excel file created: {xpath_file}")
def load_prompt_from_file(prompt_type):
    config_folder = os.path.join(os.getcwd(), "Input")
    prompt_file = ""

    if prompt_type == "Web":
        prompt_file = os.path.join(config_folder, "web_prompt.txt")
    if prompt_type == "Actionxpath":
        prompt_file = os.path.join(config_folder, "web_prompt.txt")
    elif prompt_type== "PowerBi":
        prompt_file = os.path.join(config_folder, "powerBi_prompt.txt")
    elif prompt_type== "Page_File":
        prompt_file = os.path.join(config_folder, "Page_file_prompt.txt")
    elif prompt_type== "Page_File_Action":
        prompt_file = os.path.join(config_folder, "Page_file_prompt_with_action.txt")
    elif prompt_type== "Test_File_Action":
        prompt_file = os.path.join(config_folder, "test_script_prompt.txt")
    elif prompt_type== "Test_case_generation":
        prompt_file = os.path.join(config_folder, "Testcase_generate_prompt.txt")
    elif prompt_type== "Test_case_generation_document":
        prompt_file = os.path.join(config_folder, "Testcase_generate_prompt_with_document.txt")
    elif prompt_type== "Test_case_generation_withaction":
        prompt_file = os.path.join(config_folder, "Testcase_generate_prompt_with_action.txt")
    elif prompt_type == "featureaction":
        prompt_file = os.path.join(config_folder, "featureaction_prompt.txt")
    elif prompt_type == "featurefile":
        prompt_file = os.path.join(config_folder, "featurefile_prompt.txt")
    else:
        raise ValueError(f"Invalid prompt type: {prompt_type}. Expected 'web' or 'powerBi'.")

    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found at: {prompt_file}")

    with open(prompt_file, "r", encoding="utf-8") as file:
        prompt_template = file.read()

    return prompt_template
def create_java_file(file_name: str, file_extension: str,response):
    # Ensure the file extension is .java
    if not file_extension.startswith("."):
        if file_extension =="java":
            file_extension = f".{file_extension}"
        elif file_extension =="python":
            file_extension = f".py"
        else:
            file_extension = f".{file_extension}"

    # Full file path with specified directory
    full_file_path = os.path.join(Page_file_generator, f"{file_name}{file_extension}")

    with open(full_file_path, "w") as file:
        file.write(response)

    st.write(f"✅ page file script generated: {full_file_path}")
def create_test_file(file_name: str, file_extension: str,response):
    # Ensure the file extension is .java
    if not file_extension.startswith("."):
        if file_extension =="java":
            file_extension = f".{file_extension}"
        elif file_extension =="python":
            file_extension = f".py"
        else:
            file_extension = f".{file_extension}"

    # Full file path with specified directory
    full_file_path = os.path.join(Test_file_generator, f"{file_name}{file_extension}")

    with open(full_file_path, "w") as file:
        file.write(response)

    st.write(f"✅ Test file script generated: {full_file_path}")

def get_queries_from_ai(prompt, formatted_summary):
    # Access the variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    # Set the environment variables explicitly if needed
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint

    model = AzureChatOpenAI(
        openai_api_version="2023-05-15",
        azure_deployment="qepracticekey",
    )
    prompt_template = load_prompt_from_file(prompt)
    print(prompt_template)

    if prompt == "PowerBi":
        #print("formatted_summary:", {formatted_summary})
        formatted_summary_json = json.dumps(formatted_summary, indent=2)
        final_prompt = prompt_template.format(formatted_summary=formatted_summary_json)
        print("Final prompt:", {final_prompt})
        json_list = formatted_summary if isinstance(formatted_summary, list) else json.loads(formatted_summary)
        chunk_size = 15
        json_chunks = [json_list[i:i + chunk_size] for i in range(0, len(json_list), chunk_size)]
        # Collecting responses for all JSON chunks
        all_responses = []
        for i, chunk in enumerate(json_chunks):
            print(f"Processing JSON chunk {i + 1}/{len(json_chunks)}")
            formatted_summary_json = json.dumps(chunk, indent=2)
            final_prompt = prompt_template.format(formatted_summary=formatted_summary_json)

            message = HumanMessage(content=final_prompt)
            output_value = model([message])
            print(f"Response for chunk {i + 1}: {output_value.content}")
            all_responses.append(output_value.content)

        # Combine all responses into one
        combined_response = "\n".join(all_responses)
        return combined_response
    elif prompt == "Web":
        print(formatted_summary)
        #final_prompt = prompt_template.format(formatted_summary=formatted_summary)
        prompt = f"""
From the given list of elements, generate all possible XPath expressions for each element using its tag and attributes only. 
Return only valid XPath strings as output. Do not include any explanation or description. 

Input: {formatted_summary}
"""
        message = HumanMessage(content=prompt)
        output_value = model([message])
        print(output_value)
        return output_value.content
    elif prompt == "Actionxpath":
        all_responses = []

        for page_url, page_data in formatted_summary.items():
            print(f"\n🔍 Processing page: {page_url}")

            # Get the list of elements
            elements = page_data.get("collected_elements", [])

            if not elements:
                print(f"⚠️ No elements found on {page_url}")
                continue

            # Convert elements list to JSON string
            elements_json = json.dumps(elements, indent=2)

            # Format the prompt
            final_prompt = prompt_template.format(formatted_summary=elements_json)
            print(f"📝 Final prompt for {page_url}:\n", final_prompt)

            # Pass to model
            message = HumanMessage(content=final_prompt)
            response = model([message])
            print(f"📨 Response from AI for {page_url}:\n", response.content)

            # Optional: add page name in response if needed
            response_with_context = response.content
            all_responses.append(response_with_context)

        # Return all combined responses
        return "\n\n".join(all_responses)

    elif prompt == "Page_File":
        print(formatted_summary)
        message = HumanMessage(content=formatted_summary)
        output_value = model([message])
        print(output_value)
        return output_value.content
    # Split the JSON list if its length exceeds 15

def get_queries_from_ai_duplicate(prompt,formatted_summary):
    prompt_template = load_prompt_from_file(prompt)
    print(prompt_template)

    if prompt=="PowerBI":
        print("formatted_summary:",{formatted_summary})
        formatted_summary_json = json.dumps(formatted_summary, indent=2)
        final_prompt = prompt_template.format(formatted_summary=formatted_summary_json)

    elif prompt=="Web":
        print("formatted_summary:", {formatted_summary})
        final_prompt = prompt_template.format(formatted_summary=formatted_summary)
    # Convert formatted_summary to a JSON-formatted string
    formatted_summary_json = json.dumps(formatted_summary, indent=2)

    final_prompt = prompt_template.format(formatted_summary=formatted_summary_json)
    # Collect visible elements
    os.environ["AZURE_OPENAI_API_KEY"] = "4fed2bedb59744a99b0424622f6d9d1b"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://qepracticekey.openai.azure.com/"

    model = AzureChatOpenAI(
        openai_api_version="2023-05-15",
        azure_deployment="qepracticekey",
    )
    message = HumanMessage(content=final_prompt)
    output_value = model([message])
    print(output_value)
    return output_value.content

def is_page_loaded(driver):
    return driver.execute_script("return document.readyState")
def loading_newpage(driver):
    new_page_url = driver.current_url
    print(new_page_url)
    driver.get(new_page_url)
    driver.refresh()
    WebDriverWait(driver, 30).until(is_page_loaded)

def generate_random_prefix(length=8):
    """Generate a random alphanumeric prefix."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
def generate_unique_key(element, page_identifier):
    """
    Generate a truly unique key for each visible element.
    The key is based on page identifier, tag name, ID, class, and text content (trimmed).
    """
    tag_name = element.tag_name
    element_id = element.get_attribute("id")
    element_class = element.get_attribute("class")
    element_text = element.text.strip()[:30]  # Limiting text length for clarity

    # Using unique attributes with a fallback to text if ID/Class are absent
    key_parts = [
        page_identifier,
        tag_name,
        f"id={element_id}" if element_id else "no_id",
        f"class={element_class}" if element_class else "no_class",
        f"text={element_text}" if element_text else "no_text"
    ]

    # Generate the base key
    base_key = "|".join(key_parts)

    # Ensuring uniqueness with a counter (auto-increment)
    unique_key = base_key
    counter = 1
    while unique_key in st.session_state:
        unique_key = f"{base_key}|{counter}"
        counter += 1

    return unique_key
def generate_unique_key_duplicate(element,page_identifier='page', prefix='element'):
    """Generate a unique key based on the element's properties."""
    element_str = f"{element.get_attribute('id')}-{element.tag_name}-{element.text.strip()}"
    unique_hash = hashlib.md5(element_str.encode()).hexdigest()
    # Generate the next number from the counter and format it as a 3-digit number
    # Combine prefix, unique hash, and formatted number
    #unique_uuid = uuid.uuid4().hex
    random_prefix = generate_random_prefix()
    return f"{prefix}_{page_identifier}_{unique_hash}_{random_prefix}"
def details_visible_elements(collected_elements,visible_elements,selected_tags,page_identifier):
    for idx, element in enumerate(collected_elements):
        try:
            # if element.is_displayed() and element.is_enabled():
            tag_name = element.tag_name

            # If specific tags are selected or all are allowed
            if "All" in selected_tags or tag_name in selected_tags:
                print(f"[DEBUG] Processing element {idx + 1} with tag: {tag_name}")
                details = {
                    "tag": tag_name,
                    "id": element.get_attribute("id"),
                    "class": element.get_attribute("class"),
                    "name": element.get_attribute("name"),
                    "text": element.text.strip()
                }

                # Filter out empty values
                compact_details = {k: v for k, v in details.items() if v}
                print(f"[DEBUG] Element details: {json.dumps(compact_details, indent=2)}")

                if compact_details:  # Only add if there is meaningful data
                    visible_elements.append(compact_details)

                    # Store for XPath mapping via OpenAI
                    unique_key = generate_unique_key(element, page_identifier)
                    if unique_key not in st.session_state:
                        st.session_state[unique_key] = compact_details
                        print(f"[DEBUG] Unique key stored: {unique_key}")

        except (StaleElementReferenceException, NoSuchElementException) as e:
            print(f"[WARN] Element {idx + 1} skipped due to: {str(e)}")

        except Exception as e:
            print(f"[ERROR] Unexpected error with element {idx + 1}: {str(e)}")

    print(f"[INFO] Total visible elements found inside method: {len(visible_elements)}")
    return visible_elements
def load_config(config_path=None):

    if not config_path:
        config_path = os.path.join(os.getcwd(), "Input", "config.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}. Please ensure the config file exists.")

    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict) or "xpaths" not in config:
        raise ValueError("Invalid config file format. Ensure 'xpaths' section is properly defined.")

    xpaths = config.get("xpaths", {})
    if not xpaths:
        raise ValueError("XPath values are missing in the 'xpaths' section.")

    return xpaths

def get_visible_element_powerBi(driver,page_identifier):
    # Collect visible elements
    xpaths = load_config()
    print("Loaded XPaths:", xpaths)
    # Attempt 1: Fetch svg > text nodes
    elements_svg_text = driver.find_elements(By.XPATH, xpaths["elements_svg_text"])

    # Collect elements from both visual-container and SVG text elements
    elements_visual_container = driver.find_elements(By.XPATH, xpaths["elements_visual_container"])
    # Graph specific elements
    graph_label_elements = driver.find_elements(By.XPATH,xpaths["graph_label_elements"])
    graph_tick_elements = driver.find_elements(By.XPATH,xpaths["graph_tick_elements"])
    graph_title_elements = driver.find_elements(By.XPATH,xpaths["graph_title_elements"])
    print(f"SVG text found: {len(elements_svg_text)}")
    print(f"Visual containers found: {len(elements_visual_container)}")
    print(f"Graph labels found: {len(graph_label_elements)}")
    print(f"Graph ticks found: {len(graph_tick_elements)}")
    print(f"Graph titles found: {len(graph_title_elements)}")
    # Merge the lists while avoiding duplicates
    # all_elements = list(set(elements_visual_container + elements_svg_text+graph_label_elements +
    #                         graph_tick_elements +
    #                         graph_title_elements))
    all_elements = (elements_visual_container +
                    elements_svg_text +
                    graph_label_elements +
                    graph_tick_elements +
                    graph_title_elements)
    #print(all_elements)
    visible_elements = []
    unique_elements={}


    for idx, element in enumerate(all_elements):
        try:
            if element.is_displayed() and element.is_enabled():
                tag_name = element.tag_name
                text_content = element.text.strip()
                class_name = element.get_attribute("class")
                # Generate a unique key for deduplication
                unique_key =generate_unique_key(element,"powerBi")
                # If specific tags are selected or all are allowed
                #if "All" in selected_tags or tag_name in selected_tags or tag_name in ["text", "div", "span", "a", "button"]:
                if unique_key not in unique_elements:
                    details = {
                        "tag": tag_name,
                        "id": element.get_attribute("id"),
                        "class": element.get_attribute("class"),
                        "name": element.get_attribute("name"),
                        "aria-label": element.get_attribute("aria-label"),
                        "text": element.text.strip()
                    }

                    # Include only non-empty values
                    compact_details = {k: v for k, v in details.items() if v}

                    if compact_details:
                        visible_elements.append(compact_details)
                        unique_elements[unique_key] = compact_details
                        # Store for XPath mapping via OpenAI
                        session_key = generate_unique_key(element, page_identifier)
                        if unique_key not in st.session_state:
                            st.session_state[session_key] = compact_details

        except (StaleElementReferenceException, NoSuchElementException):
            continue

    print(json.dumps(visible_elements, indent=2))
    print(f"[INFO] Total visible elements found: {len(visible_elements)}")
    return visible_elements

def get_visible_element_iframe(driver, page_identifier, selected_tags):
    visible_elements = []  # To store visible and relevant elements

    print("[INFO] Collecting all elements from the main page...")
    all_elements = driver.find_elements(By.XPATH, "//*")
    print(f"[DEBUG] Total elements on main page: {len(all_elements)}")
    #total_elements.extend(all_elements)

    # Collect elements from each iframe
    iframe_elements = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"[INFO] Total iframes found: {len(iframe_elements)}")
    if len(iframe_elements) > 0:
        for iframe_index, iframe_element in enumerate(iframe_elements):
            print(f"[INFO] Switching to iframe {iframe_index + 1}...")
            try:
                driver.switch_to.frame(iframe_element)
                iframe_subelements = driver.find_elements(By.XPATH, "//*")
                details_visible_elements(iframe_subelements,visible_elements,selected_tags,page_identifier)
                print(f"[DEBUG] Total elements in iframe {iframe_index + 1}: {len(iframe_subelements)}")
            except Exception as e:
                print(f"[WARN] Failed to switch to iframe {iframe_index + 1}: {str(e)}")
            finally:
                try:
                    driver.switch_to.default_content()  # Return to the main page
                except Exception as e:
                    print(f"[ERROR] Failed to switch back to main content: {str(e)}")
    else:
        print("[INFO] No iframes found, directly collecting main page elements...")

    visible_elements=details_visible_elements(all_elements,visible_elements,selected_tags,page_identifier)
    # Return the list of visible, relevant elements
    print(f"[INFO] Total visible elements found: {len(visible_elements)}")
    print(json.dumps(visible_elements, indent=2))
    return visible_elements


def get_visible_element(driver,page_identifier,selected_tags):
    all_elements = driver.find_elements(By.XPATH, "//*")
    visible_elements = []


    # Loop through elements and capture only relevant ones
    for idx, element in enumerate(all_elements):
        try:
            # Ensure the element is visible and not disabled
            if element.is_displayed() and element.is_enabled():

                # Check if the element is a relevant type (text box, checkbox, button, link)
                if element.tag_name in selected_tags:
                    #, 'textarea', 'button', 'select'
                    details = {
                        "tag": element.tag_name,
                        "id": element.get_attribute("id"),
                        "class": element.get_attribute("class"),
                        "name": element.get_attribute("name"),
                        "text": element.text.strip()
                    }

                    # Exclude empty or redundant text (only keep the most relevant ones)
                    compact_details = {k: v for k, v in details.items() if v}

                    # Add to the list of visible elements
                    visible_elements.append(compact_details)
                    # Generate a unique key for each element
                    unique_key = generate_unique_key(element, page_identifier)
                    if unique_key not in st.session_state:
                        st.session_state[unique_key] = unique_key

        except (StaleElementReferenceException, NoSuchElementException) as e:
            # Handle exceptions
            #print(f"Element skipped due to: {e}")
            continue

    # Return the list of visible, relevant elements
    print(visible_elements)
    return visible_elements



key=None
def selecting_xpath(details):

    sections = details.strip().split('\n\n')
    print("sections is displayed as:")
    print(sections)
    xpath_dict = {}
    for section in sections:
        print("section is displayed " +section)
        xpaths=[]
        global key
        #key = None
        if '\n' in section:
            lines = section.split('\n')
            print("Lines are displaed as")
            print(lines)
            if lines:
                #key = lines[0].replace(" Variations:", "")
                #print("key is displayed as"+key)
                if "//" in lines[0]:
                    xpaths = lines
                else:
                    xpaths = lines[1:]
                print("xpatha are displayed as")
                print(xpaths)
        else:
            key=section
            print("key is displayed as" + key)
        if xpaths:
            if key:
                print("key available:",key)
                xpath_dict[key] = xpaths
                key = None
            elif key is None:
                print("key not available", key)
                key = lines[0].replace(" Variations:", "")
                print("key from lines", key)
                xpath_dict[key] = xpaths
                key=None
    print("xpath_dict:",xpath_dict)
    return xpath_dict

# Filter out duplicate xpaths before passing to UI
def filter_duplicate_xpaths(xpath_dict):
    unique_entries = set()
    filtered_xpath_dict = {}

    for element, xpaths in xpath_dict.items():
        filtered = []
        for xpath in xpaths:
            key = f"{element}_{xpath}"
            if key not in unique_entries:
                unique_entries.add(key)
                filtered.append(xpath)
        if filtered:
            filtered_xpath_dict[element] = filtered
    return filtered_xpath_dict
def adding_xapth_user_view(xpath_dict):
    print("goind to add element")
    try:
        for element, xpaths in xpath_dict.items():
            st.subheader(f"{element}")
            for xpath in xpaths:
                if xpath.strip():
                    # unique_id = uuid.uuid4().hex[:8]
                    # checkbox_key = f"{element}_{xpath}_{unique_id}"
                    checkbox_key = hashlib.md5(f"{element}_{xpath}".encode()).hexdigest()
                    # Display checkbox and maintain state
                    print("st.session_state.selected_xpaths", st.session_state.selected_xpaths)
                    try:
                        if st.checkbox(xpath, key=checkbox_key):
                            print("st.session_state.selected_xpaths", st.session_state.selected_xpaths)
                            if {"Element": element, "XPath": xpath} not in st.session_state.selected_xpaths:
                                st.session_state.selected_xpaths.append({"Element": element, "XPath": xpath})
                        else:
                            print("st.session_state.selected_xpaths", st.session_state.selected_xpaths)
                            st.session_state.selected_xpaths = [
                                x for x in st.session_state.selected_xpaths if x["XPath"] != xpath
                            ]
                    except Exception as e:
                        print("st.session_state.selected_xpaths", st.session_state.selected_xpaths)
                        #print(e)
                    except (Exception) as e:
                        print("st.session_state.selected_xpaths", st.session_state.selected_xpaths)
        print("st.session_state.selected_xpaths_final", st.session_state.selected_xpaths)
        return st.session_state.selected_xpaths
    except (Exception) as e:
        return st.session_state.selected_xpaths
        print(e)

def adding_selected_xapth_excel(new_page_name,):
    for item in st.session_state.selected_xpaths:
        item['Page Name'] = new_page_name

    excel_file = xpath_file
    if os.path.exists(excel_file):
        # Read existing file
        existing_df = pd.read_excel(excel_file, engine='openpyxl')
    else:
        existing_df = pd.DataFrame()
    new_df = pd.DataFrame(st.session_state.selected_xpaths)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['XPath', 'Page Name'], keep='last')

    # Save the combined DataFrame back to the Excel file
    combined_df.to_excel(excel_file, index=False, engine='openpyxl')
    st.success(f"XPaths successfully added to Excel! Download the file [here](sandbox:{excel_file})")
def clean_xpath(xpath):
    """Extracts only the actual XPath from a given string."""
    match = re.search(r'(//[^\]]+\])', xpath)  # Find everything starting with // until the first ]
    return match.group(1) if match else xpath  # Return extracted XPath or original if not found
def generate_excel_testcases_with_document(prompt_type,extracted_data):
    prompt_template = load_prompt_from_file(prompt_type)
    # Conditionally inject Action Data section or leave it blank
    final_prompt = prompt_template.format(requirements=extracted_data)
    print(final_prompt)
    return final_prompt
def generate_pom_from_excel_testcases(prompt_type,navigation,image_data,action_data=None,requirements=""):
    prompt_template = load_prompt_from_file(prompt_type)
    # Conditionally inject Action Data section or leave it blank
    if action_data:
        action_section = f"- User Interaction Elements (Action Data): {action_data}"
    else:
        action_section = ""
    final_prompt = prompt_template.format(navigation=navigation,image_data_processed=image_data,action_data_processed=action_section,requirements=requirements)
    print(final_prompt)
    return final_prompt
def generate_pom_from_excel_feature(prompt_type,Recorded_Action):
    prompt_template = load_prompt_from_file(prompt_type)
    final_prompt = prompt_template.format(recorded_action=Recorded_Action)
    print(final_prompt)
    return final_prompt
def generate_test_script(prompt_type,test_file_language,page_file_conetent,test_file_content):
    prompt_template = load_prompt_from_file(prompt_type)
    final_prompt = prompt_template.format(test_file_language=test_file_language,page_files_content=page_file_conetent,test_files_content=test_file_content)
    print(final_prompt)
    return final_prompt
def generate_pom_from_excel_with_action(prompt_type,page_name,language,action_data):
    prompt_template = load_prompt_from_file(prompt_type)
    print(prompt_template)
    # Read Excel file
    excel_file = xpath_file
    if not os.path.exists(excel_file):
        print(f"Excel file not found: {excel_file}")
        return


    df = pd.read_excel(excel_file)

    # Check if required columns exist
    if not {"Element", "XPath", "Page Name"}.issubset(df.columns):
        print("Excel file is missing required columns: Element, XPath, Page Name")
        return

    # Filter XPaths based on Page Name
    filtered_df = df[df["Page Name"] == page_name]

    if filtered_df.empty:
        print(f"No elements found for page: {page_name}")
        return

    # Extract XPaths
    xpaths = "\n".join(filtered_df["XPath"].apply(clean_xpath).tolist())
    final_prompt = prompt_template.format(language=language,xpaths=xpaths,Action_data=action_data)
    print(final_prompt)
    return final_prompt
def generate_pom_from_excel(prompt_type,page_name,language):
    prompt_template = load_prompt_from_file(prompt_type)
    print(prompt_template)
    # Read Excel file
    excel_file = xpath_file
    if not os.path.exists(excel_file):
        print(f"Excel file not found: {excel_file}")
        return


    df = pd.read_excel(excel_file)

    # Check if required columns exist
    if not {"Element", "XPath", "Page Name"}.issubset(df.columns):
        print("Excel file is missing required columns: Element, XPath, Page Name")
        return

    # Filter XPaths based on Page Name
    filtered_df = df[df["Page Name"] == page_name]

    if filtered_df.empty:
        print(f"No elements found for page: {page_name}")
        return

    # Extract XPaths
    xpaths = "\n".join(filtered_df["XPath"].apply(clean_xpath).tolist())

    final_prompt = prompt_template.format(language=language,xpaths=xpaths)
    print(final_prompt)
    return final_prompt
def scroll_and_focus():
    st.markdown("""
        <script>
        setTimeout(function() {
            const topElement = document.querySelector("a[name='top-button']");
            if (topElement) {
                topElement.scrollIntoView({ behavior: "smooth" });
            }
            const buttons = Array.from(document.querySelectorAll('button'));
            const collectButton = buttons.find(btn => btn.innerText.trim() === 'Collecting Elements');
            if (collectButton) {
                collectButton.focus();
            }
        }, 500);
        </script>
    """, unsafe_allow_html=True)

def select_and_read_text_files(folder_path):
    # Step 1: List all .txt files in the folder
    txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

    if not txt_files:
        st.warning("No .txt files found in the folder.")
        return {}

    # Step 2: Let the user select multiple files
    selected_files = st.multiselect("Please select relevent action file ", txt_files)

    # Step 3: Read contents of selected files
    file_contents = {}
    for file_name in selected_files:
        full_path = os.path.join(folder_path, file_name)
        with open(full_path, 'r', encoding='utf-8') as f:
            file_contents[file_name] = f.read()

    # Step 4: Return dictionary of filename: content
    return file_contents

def monitor_url_changes(driver, screenshot_folder, stop_flag):
    last_url = ""
    while not stop_flag["stop"]:
        try:
            current_url = driver.current_url
            if current_url != last_url:
                last_url = current_url
                filepath = action_utils.take_screenshot(driver, screenshot_folder)
                print(f"📸 Screenshot taken for: {current_url} => {filepath}")
        except Exception as e:
            print("Error during URL monitoring:", e)
        time.sleep(1)  # check every second
def select_and_read_text_files_xpath(type, folder_path):
    # Step 1: List all files in the folder
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    if not files:
        st.warning("No files found in the folder.")
        return {}

    selected_files = st.multiselect(f"Select relevant file(s) for {type.replace('_', ' ')}", files)

    file_contents = {}

    for file_name in selected_files:
        full_path = os.path.join(folder_path, file_name)

        try:
            # Type: For txt-based files
            if type in ["xpath", "page", "feature"]:
                with open(full_path, 'r', encoding='utf-8') as f:
                    file_contents[file_name] = f.read()


            elif type == "page_test" and file_name.endswith(".py"):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Remove common Markdown wrappers
                    if content.startswith("```python"):
                        content = content.split("```python", 1)[1]
                    if "```" in content:
                        content = content.split("```", 1)[0]

                    try:
                        tree = ast.parse(content)
                        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                        file_contents[file_name] = functions
                    except SyntaxError as syntax_err:
                        st.error(
                            f"Syntax error in {file_name}:\nLine {syntax_err.lineno} - {syntax_err.text.strip() if syntax_err.text else ''}")
                        continue

                except Exception as read_err:
                    st.error(f"Failed to read {file_name}: {read_err}")

            # Type: For Excel test cases - testcase_test
            elif type == "testcase_test" and file_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(full_path)

                test_case_name = df['Test Case Name'][0]
                page_name = df['Page'][0] if 'Page' in df.columns else None
                actions = df['Action'].dropna().tolist() if 'Action' in df.columns else []
                expected = df['Expected Result'].dropna().tolist() if 'Expected Result' in df.columns else []

                file_contents[file_name] = {
                    "test_case_name": test_case_name,
                    "page_name": page_name,
                    "actions": actions,
                    "expected_results": expected
                }

            else:
                st.warning(f"Unsupported or mismatched file type for {file_name}")

        except Exception as e:
            st.error(f"Error processing {file_name}: {e}")

    return file_contents


def get_queries_from_ai_updated(formatted_summary):
    # Access the variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    # Set the environment variables explicitly if needed
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint

    model = AzureChatOpenAI(
        openai_api_version="2023-05-15",
        azure_deployment="qepracticekey",
    )
    message = HumanMessage(content=formatted_summary)
    output_value = model([message])
    print(output_value)
    return output_value.content
def markdown_to_dataframe(markdown_text):
    # Extract lines that look like markdown rows
    lines = markdown_text.strip().splitlines()
    table_lines = [line for line in lines if "|" in line and not line.strip().startswith("---")]

    if len(table_lines) < 2:
        print("⚠️ No valid markdown table found.")
        return pd.DataFrame()

    # Clean up each line
    cleaned_lines = [re.sub(r"^\s*\|\s*|\s*\|\s*$", "", line).strip() for line in table_lines]
    cleaned_lines = [re.sub(r"\s*\|\s*", ",", line) for line in cleaned_lines]

    csv_data = "\n".join(cleaned_lines)

    print("🔍 Cleaned CSV-like content:\n", csv_data)

    # Use StringIO to load into DataFrame
    try:
        df = pd.read_csv(StringIO(csv_data))
        return df
    except Exception as e:
        print(f"❌ Failed to convert markdown to DataFrame: {e}")
        return pd.DataFrame()
def covert_response_to_testcases(markdown_text,test_collection):
    # STEP 1: Strip markdown code fencing (``` or ```markdown)
    if markdown_text.startswith("```"):
        markdown_text = "\n".join(
            line for line in markdown_text.splitlines()
            if not line.strip().startswith("```")
        )
    # STEP 2: Clean and parse markdown table
    lines = markdown_text.strip().split('\n')
    cleaned_lines = [line for line in lines if not set(line.strip()).issubset(set('|- '))]
    cleaned_text = "\n".join(cleaned_lines)

    df = pd.read_csv(StringIO(cleaned_text), sep='|', engine='python')
    df = df.dropna(axis=1, how='all')
    df.columns = [col.strip() for col in df.columns]
    # df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

    # STEP 3: Fill missing Test Case Names
    df['Test Case Name'] = df['Test Case Name'].replace('', pd.NA).ffill()


    # STEP 5: Write each test case into a separate Excel file
    for test_case, group in df.groupby("Test Case Name"):
        file_name = f"{test_case.strip()[:50]}.xlsx"  # Truncate for safety
        safe_file_name = "".join(c for c in file_name if c.isalnum() or c in "._- ()").rstrip()
        path = os.path.join(test_collection, safe_file_name)
        group.to_excel(path, index=False)

    print(f"✅ Created individual Excel files in folder: {output_folder}")


def create_testcase_in_Excel(raw_response, test_location):
    os.makedirs(test_location, exist_ok=True)

    df = markdown_to_dataframe(raw_response)

    if df.empty:
        print("⚠️ No test cases found in the markdown.")
        return

    print("✅ Parsed DataFrame:\n", df)

    for name, group in df.groupby("Test Case Name"):
        safe_name = name.replace(" ", "_").replace("/", "_").strip()
        file_path = os.path.join(test_location, f"{safe_name}.xlsx")
        group.to_excel(file_path, index=False)

    print(f"✅ {len(df['Test Case Name'].unique())} test cases saved in: {test_location}")

import io
def extract_testcase_context_from_excel_file(file_obj):
    try:
        # If it's a string (file path), let pandas handle it
        if isinstance(file_obj, str):
            df = pd.read_excel(file_obj)

        # If it's a file-like object (e.g., from Streamlit), decode to BytesIO
        else:
            file_bytes = file_obj.read()
            df = pd.read_excel(io.BytesIO(file_bytes))

        test_case_name = df['Test Case Name'][0]
        page_name = df['Page'][0] if 'Page' in df.columns else None
        actions = df['Action'].dropna().tolist() if 'Action' in df.columns else []
        expected = df['Expected Result'].dropna().tolist() if 'Expected Result' in df.columns else []

        return {
            "test_case_name": test_case_name,
            "page_name": page_name,
            "actions": actions,
            "expected_results": expected
        }

    except Exception as e:
        print(f"❌ Error extracting test case context: {e}")
        return {
            "test_case_name": "",
            "page_name": "",
            "actions": [],
            "expected_results": []
        }
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
def extract_text_from_pdf(uploaded_pdf):
    text = ""
    pdf_reader = PyPDF2.PdfReader(uploaded_pdf)
    num_pages = len(pdf_reader.pages)
    for page_number in range(num_pages):
        page = pdf_reader.pages[page_number]
        # Extract text and remove non-alphanumeric characters
        text += re.sub(r'\W+', ' ', page.extract_text())
    print("text extracted"+text)
    return text


def get_queries_from_ai_file_extract(uploaded_pdf):
    os.environ["AZURE_OPENAI_API_KEY"] = "4fed2bedb59744a99b0424622f6d9d1b"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://qepracticekey.openai.azure.com/"
    extracted_text = extract_text_from_pdf(uploaded_pdf)

    val2 = """
Act as Functional Test Case Generator. Based on a given Requirement, create detailed and comprehensive test cases using the Orthogonal Array technique. Each test case should have multiple steps, covering a sequence of actions to verify functionality. Use the following columns in the output Excel sheet: 
- Test Case Name
- Step Number
- Test Step Description
- Test Step Expected Result
- Status (set as 'New')
- Type (set as 'Manual') 

Ensure that each test case contains:
- Multiple detailed steps with clear descriptions of actions to perform.
- Expected results for each step, specifying the criteria for a successful outcome.
- Coverage of both Positive and Negative scenarios, highlighting edge cases and valid/invalid inputs.
- Sequential numbering of steps, ensuring clarity in the flow of operations.
- The final test cases should verify all combinations of parameters from the Orthogonal Array, ensuring exhaustive coverage of pairwise interactions.

Format:
-Table

Include examples where applicable.
Create the test cases in the similar format with the following requirement:
""" + extracted_text[:8000]

    model = AzureChatOpenAI(
        openai_api_version="2023-05-15",
        azure_deployment="qepracticekey",
    )
    message = HumanMessage(
        content=val2
    )
    output_value = model([message])
    return (output_value.content)


def extract_page_file_info_from_file(file_obj):
    try:
        # Read actual content of the file
        content = file_obj.read().decode('utf-8')  # decode if it's a file-like object from Streamlit

        # Parse the code content, not the file name
        tree = ast.parse(content)

        methods = []
        xpaths = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.append(node.name)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                        val_str = ast.unparse(node.value)
                        if "xpath" in val_str.lower():
                            xpaths.append((target.id, val_str))

        return {
            "methods": methods,
            "xpaths": xpaths
        }

    except Exception as e:
        print(f"Error parsing file: {e}")
        return {
            "methods": [],
            "xpaths": []
        }