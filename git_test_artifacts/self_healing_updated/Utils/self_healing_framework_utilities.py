import os
import re
import json
import docx2txt
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()

api_key  = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"]  = api_key
os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint


def _llm():
    return AzureChatOpenAI(openai_api_version="2023-05-15", azure_deployment="qepracticekey")


def run_mcp_prompt_compare(prompt_file, replace_dict=None):
    with open(prompt_file, 'r', encoding='utf-8') as f:
        template = f.read()
    if replace_dict:
        for key, value in replace_dict.items():
            if not isinstance(value, str):
                value = json.dumps(value)
            template = template.replace(key, value)
    return template


def read_workflow_document(file_path):
    """Read action file — supports .txt and .docx."""
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
    """Extract XPaths from an Object Repository file using LLM."""
    prompt = run_mcp_prompt_compare(
        'input/framework_prompt/read_OR_file.txt',
        {'{content}': content}
    )
    return _llm().invoke([HumanMessage(content=prompt)]).content.strip()


def collect_xpath_from_page_file(page_file_content):
    """Extract XPaths from a page object file using LLM."""
    prompt = run_mcp_prompt_compare(
        'input/framework_prompt/read_pagefile.txt',
        {'{page_file_content}': page_file_content}
    )
    return _llm().invoke([HumanMessage(content=prompt)]).content.strip()


def generate_page_wise_xpath(page_name, page_references, or_response=None):
    """Combine page file XPaths with OR XPaths into a clean page-level list."""
    prompt = run_mcp_prompt_compare(
        'input/framework_prompt/generate_xpath.txt',
        {
            '{page_name}':       page_name,
            '{page_references}': page_references,
            '{or_response}':     or_response or ""
        }
    )
    return _llm().invoke([HumanMessage(content=prompt)]).content.strip()


def generate_xpath_doc(xpath_file_path, page_folder_path):
    """
    Extract all XPaths from local page files and optional OR file.
    Writes generated_xpath_details/xpath_details.json.
    """
    output_folder = "generated_xpath_details"
    os.makedirs(output_folder, exist_ok=True)
    json_path = os.path.join(output_folder, "xpath_details.json")

    or_dict = ""
    # OR file
    if xpath_file_path and xpath_file_path.lower() != "none" and os.path.exists(xpath_file_path):
        with open(xpath_file_path, 'r', encoding='utf-8') as f:
            or_content = f.read()
        or_dict = collect_xpath_from_external_file(or_content)
        json_obj = json.loads(or_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_obj, f, indent=4, ensure_ascii=False)
        print(f"✅ OR XPath JSON created: {json_path}")

    # Page files
    result = {}
    if page_folder_path and os.path.exists(page_folder_path):
        for filename in os.listdir(page_folder_path):
            if not filename.endswith('.py'):
                continue
            full_path = os.path.join(page_folder_path, filename)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            xpath_page_file = collect_xpath_from_page_file(content)
            if not xpath_page_file.strip():
                continue
            page_name = os.path.splitext(filename)[0]
            page_xpath = generate_page_wise_xpath(page_name, xpath_page_file, or_dict)
            result[page_name] = [x.strip() for x in page_xpath.splitlines()]

        output_data = {page: xpaths for page, xpaths in result.items()}
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"✅ Page XPath JSON created: {json_path}")
