import os
import re
import docx2txt
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from src.mcp_use_client import *
import json
### Load env ####
from dotenv import load_dotenv
load_dotenv()

 # Access the variables
api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
# Set Azure OpenAI credentials
os.environ["AZURE_OPENAI_API_KEY"] = api_key
os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint 


def run_mcp_prompt_compare(prompt_file, replace_dict=None):
    """Helper to read prompt, replace variables, and execute MCP."""
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    if replace_dict:
        for key, value in replace_dict.items():
            if not isinstance(value, str):
                value = json.dumps(value)  # convert non-string to string
            prompt_template = prompt_template.replace(key, value)
    return prompt_template

def read_workflow_document(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Workflow file not found: {file_path}")

    if file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_path.endswith(".docx"):
        return docx2txt.process(file_path)
    else:
        raise ValueError("Unsupported file type. Only .txt and .docx are supported.")


def collect_xpath_from_external_file(content):
    model = AzureChatOpenAI(openai_api_version="2023-05-15", azure_deployment="qepracticekey")
    script_text = run_mcp_prompt_compare(
        'input/framework_prompt/read_OR_file.txt',
        {
            '{content}': content,
        }
    )
    return model.invoke([HumanMessage(content=script_text)]).content.strip()


def collect_xpath_from_page_file(page_file_content):
    model = AzureChatOpenAI(openai_api_version="2023-05-15", azure_deployment="qepracticekey")
    script_text = run_mcp_prompt_compare(
        'input/framework_prompt/read_pagefile.txt',
        {
            '{page_file_content}': page_file_content,
        }
    )
    return model.invoke([HumanMessage(content=script_text)]).content.strip()


def generate_page_wise_xpath(page_name, page_references,or_response=None):
    print(or_response)
    print(page_name)
    print(page_references)
    model = AzureChatOpenAI(openai_api_version="2023-05-15", azure_deployment="qepracticekey")
    script_text = run_mcp_prompt_compare(
        'input/framework_prompt/generate_xpath.txt',
        {
            '{page_name}': page_name,
            '{page_references}': page_references,
            '{or_response}':or_response
        }
    )
    return model.invoke([HumanMessage(content=script_text)]).content.strip()


def extract_workflow_details(workflow_content):
    model = AzureChatOpenAI(openai_api_version="2023-05-15", azure_deployment="qepracticekey")
    prompt = f"""
You are an expert test analyst.

Your task is to extract workflow details for each application page from the given workflow document.

Instructions:
1. Identify distinct pages/screens in the flow (e.g., Login Page, Product Page).
2. For each page, extract:
   - User interactions (clicks, inputs, selections).
   - Navigation to next page (if any).
3. Maintain the correct sequence of pages as per the workflow.
4. Format your output like this:

Page: <Page Name>
- Step 1: <action>
- Step 2: <action>
...
- Navigates to: <Next Page>

Repeat this structure for all pages.

Workflow Document:
{workflow_content}
"""
    return model.invoke([HumanMessage(content=prompt)]).content.strip()


def workflow_feature_file(page_workflow):
    model = AzureChatOpenAI(openai_api_version="2023-05-15", azure_deployment="qepracticekey")
    script_text = run_mcp_prompt_compare(
        'input/framework_prompt/feature_file_generate.txt',
        {
            '{page_workflow}': page_workflow,
        }
    )
    
    return model.invoke([HumanMessage(content=script_text)]).content.strip()


def write_feature_file(page_name, feature_content, output_folder="generated_features"):
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(output_folder, f"{page_name.lower().replace(' ', '_')}.feature")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(feature_content)

    print(f"✅ Feature file generated for {page_name}: {file_path}")
    return file_path
def convert_to_json(or_dict: str, output_file="output.json"):
    # Remove code block markers (```yaml ... ```)
    cleaned = re.sub(r"```[a-zA-Z]*", "", or_dict).strip("` \n")

    data = {}
    current_key = None

    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue

        # Detect section headers (ending with :)
        if line.endswith(":"):
            current_key = line[:-1].strip().lower()
            # special case: normalize "_page" suffix for login
            if "login" in current_key and not current_key.endswith("_page"):
                current_key = current_key + "_page"
            data[current_key] = []
        elif line.startswith('"') and line.endswith('"') and current_key:
            # Add XPath values
            data[current_key].append(line.strip('"'))

    # Save as JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return data

def generate_xpath_doc(xpath_file_path, page_folder_path):

    output_folder = "generated_xpath_details"
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(output_folder, "xpath_details.json")


    or_dict = ""
    if xpath_file_path is not None:
        if xpath_file_path and os.path.exists(xpath_file_path):
            with open(xpath_file_path, 'r', encoding='utf-8') as f:
                or_content = f.read()
            or_dict = collect_xpath_from_external_file(or_content)
            #json_data = convert_to_json(or_dict)
                # Write JSON file
            json_obj = json.loads(or_dict)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_obj, f, indent=4, ensure_ascii=False)
            
            print(f"\n✅ XPath JSON document created successfully: {file_path}")
           



    result = {}
    no_page_details = []
    if page_folder_path and os.path.exists(page_folder_path):
        for filename in os.listdir(page_folder_path):
            if filename.endswith('.py'):
                full_path = os.path.join(page_folder_path, filename)
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    xpath_page_file = collect_xpath_from_page_file(content)

                    if not xpath_page_file.strip():
                        continue  # Skip if no XPath found

                    page_name = os.path.splitext(filename)[0]
                    page_xpath = generate_page_wise_xpath(page_name, xpath_page_file,or_dict)
                    result[page_name] = page_xpath.splitlines()
                    print(result)
                    
        # Prepare final JSON structure
        output_data = {}
        for page, xpaths in result.items():
            output_data[page] = [xpath.strip() for xpath in xpaths]
        
        if no_page_details:
            output_data["No Page Details"] = [xpath.strip() for xpath in no_page_details]
        
        # Write JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ XPath JSON document created successfully: {file_path}")
       


