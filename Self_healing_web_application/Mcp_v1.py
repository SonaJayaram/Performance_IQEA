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
import Utils.Self_healing_utilities as self_heling_utilities
# Set Azure OpenAI credentials
os.environ["AZURE_OPENAI_API_KEY"] = "4fed2bedb59744a99b0424622f6d9d1b"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://qepracticekey.openai.azure.com/"
OUTPUT_DIR = "output/sauce_demo"
SCRIPT_PATH = os.path.join(OUTPUT_DIR, "sauce_demo_dom_collector.js")

async def run_mcp_prompt(prompt_file, replace_dict=None):
    """Helper to read prompt, replace variables, and execute MCP."""
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    if replace_dict:
        for key, value in replace_dict.items():
            prompt_template = prompt_template.replace(key, value)

    return await execute_mcp_use(prompt_template)
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
async def run_mcp_prompt_compare_mcp(prompt_file, replace_dict=None):
    """Helper to read prompt, replace variables, and execute MCP."""
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    if replace_dict:
        for key, value in replace_dict.items():
            if not isinstance(value, str):
                value = json.dumps(value)  # convert non-string to string
            prompt_template = prompt_template.replace(key, value)
    return await execute_mcp_use(prompt_template)
async def compare(xpath_content,dom_content):
    print('Starting MCP client and server...')
    await start_mcp_client()
    script_text = await run_mcp_prompt_compare_mcp(
        'input/validte_xpath_mcp.txt',
        {
            '{dom_file_path}': dom_content,
            '{xpath_file_path}': xpath_content
        }
    )

    # Close MCP (we don’t need it for execution)
    close_mcp_client()
    print('MCP client closed.')
async def main():
    print('Starting MCP client and server...')
    await start_mcp_client()

    # STEP 1: Read feature file
    with open('sauce_demo.feature', 'r', encoding='utf-8') as f:
        gherkin_data = f.read()

    # STEP 2: Generate Playwright script from feature file via MCP
    print('Generating Playwright script from feature file...')
    script_text = await run_mcp_prompt(
        'input/mcp_execute_prompt.txt',
        {'{gherkin_data}': gherkin_data}
    )

    # Close MCP (we don’t need it for execution)
    close_mcp_client()
    print('MCP client closed.')

    # STEP 3: Save the generated script locally
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(SCRIPT_PATH, 'w', encoding='utf-8') as f:
        clean_script = script_text.strip()
        if clean_script.startswith("```"):
            clean_script = "\n".join(
                line for line in clean_script.splitlines()
                if not line.strip().startswith("```")
            )
        f.write(clean_script)
    print(f"✅ Playwright script saved to: {SCRIPT_PATH}")
def read_json_file(file_path):
    """Read and return JSON content from a given file path."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
def split_xpath_page_wise(content):
    model = AzureChatOpenAI(openai_api_version="2023-05-15", azure_deployment="qepracticekey")
    script_text = run_mcp_prompt_compare(
        'input/Xpath_page_wise.txt',
        {
            '{content}': dom_content
            
        }
    )
    #print(model([HumanMessage(content=script_text)]).content.strip())
    return model([HumanMessage(content=script_text)]).content.strip()

def compare_xpathdetails_dom(xpath_content,dom_content):
    # xpath_chunks=split_xpath_page_wise(xpath_content)
    # dom_chunks=split_xpath_page_wise(dom_content)
    model = AzureChatOpenAI(openai_api_version="2023-05-15", azure_deployment="qepracticekey")
    #for dom_chunk,xpath_chunk in dom_chunks,xpath_chunks:
    script_text = run_mcp_prompt_compare(
        'input/validte_xpath.txt',
        {
            '{dom_content}': dom_content,
            '{xpath_content}': xpath_content
        }
    )
    #print(model([HumanMessage(content=script_text)]).content.strip())
    return model([HumanMessage(content=script_text)]).content.strip()

import os
import re
import pandas as pd
from io import StringIO

def save_ai_response_to_excel(ai_response_list, output_folder="validated_xpath", file_name="validated_xpath.xlsx"):
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, file_name)

    all_dfs = []

    for response in ai_response_list:
        if not isinstance(response, str):
            continue

        # Remove backticks/code fences if present
        clean_text = re.sub(r"```[a-zA-Z]*", "", response).replace("```", "").strip()

        # Only process if it looks like a markdown table
        if "|" in clean_text and "---" in clean_text:
            try:
                df = pd.read_csv(StringIO(clean_text), sep="|", engine="python")

                # Drop empty columns (caused by leading/trailing pipes in markdown)
                df = df.dropna(axis=1, how="all")

                # Clean up column names
                df.columns = [c.strip() for c in df.columns]

                # Strip whitespace in all cells
                df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

                # Skip header-only frames
                if len(df) > 0:
                    all_dfs.append(df)
            except Exception as e:
                print(f"⚠️ Skipped invalid table format: {e}")

    if not all_dfs:
        print("❌ No valid tables found in AI response.")
        return

    # Concatenate all tables into a single sheet
    final_df = pd.concat(all_dfs, ignore_index=True)

    final_df.to_excel(output_path, index=False, sheet_name="Validated_XPaths")
    print(f"✅ Saved {len(final_df)} rows into {output_path}")



def normalize_name(name: str) -> str:
    """Normalize page names for comparison."""
    return name.lower().replace("_page", "").replace("page", "").strip()

def build_dom_dict(dom_content_all):
    """Convert list of dom pages into dict {page_name: html}."""
    if isinstance(dom_content_all, list):
        return {entry["page_name"]: entry["html"] for entry in dom_content_all if "page_name" in entry}
    return dom_content_all  # already dict

def match_xpath_and_dom(xpath_content_all, dom_content_all):
    """
    Match page names between xpath_content_all and dom_content_all.
    Returns dict mapping xpath_page -> (xpath_details, dom_details_list, matched_dom_page).
    """
    dom_dict = build_dom_dict(dom_content_all)
    results = {}

    xpath_pages = list(xpath_content_all.keys())
    dom_pages = list(dom_dict.keys())

    for xpath_page in xpath_pages:
        norm_xpath = normalize_name(xpath_page)
        norm_dom_pages = [normalize_name(p) for p in dom_pages]

        # find closest match
        match = difflib.get_close_matches(norm_xpath, norm_dom_pages, n=1, cutoff=0.5)
        if match:
            dom_page = dom_pages[norm_dom_pages.index(match[0])]
            results[xpath_page] = {
                "xpath_details": xpath_content_all[xpath_page],
                "dom_details_list": dom_dict[dom_page],   
                "matched_dom_page": dom_page
            }
        else:
            results[xpath_page] = {
                "xpath_details": xpath_content_all[xpath_page],
                "dom_details_list": None,   
                "matched_dom_page": None
            }

    return results


page_keywords = {
    "self_login": ["login_page"],
    "self_logout": ["logout"],
    "self_inventory": ["inventory_page"],
    "self_cart":["shopping_cart_page"],
    "self_checkout":["checkout_page"], 
     "self_confirmation":["order_confirmation_page"]
}
def normalize_content(content, details_key=None):
    """
    Normalize content into a dictionary with page_name as key and details as value.
    - If content is a dict (like xpath_file): use keys as page names.
    - If content is a list of dicts (like dom_file): extract 'page_name'.
    """
    normalized = {}

    if isinstance(content, dict):
        # For xpath_file
        for page_name, details in content.items():
            if details_key:
                normalized[page_name] = {details_key: details}
            else:
                normalized[page_name] = details

    elif isinstance(content, list):
        # For dom_file
        for entry in content:
            page_name = entry.get("page_name")
            if not page_name:
                continue
            if details_key:
                normalized[page_name] = {details_key: entry}
            else:
                normalized[page_name] = entry

    else:
        raise TypeError("Unsupported content type for normalization")

    return normalized



def has_partial_word_match(name1, name2, skip_words=None):
    if skip_words is None:
        skip_words = {"page"}  # add more generic words if needed
    
    words1 = [w for w in re.split(r'[_\W]+', name1.lower()) if w and w not in skip_words]
    words2 = [w for w in re.split(r'[_\W]+', name2.lower()) if w and w not in skip_words]

    return any(w1 in words2 or w2 in words1 for w1 in words1 for w2 in words2)
def replace_invalid_xpaths(excel_path, target_file=None, page_folder=None):
    """
    Replace invalid XPaths in Object Repository or Page files.
    
    Args:
        excel_path (str): Path to Excel file with [Xpath, Page_Name, Status, Alternative_Xpath].
        target_file (str): Path to OR file (if exists).
        page_folder (str): Path to page files folder (if OR not provided).
    """
    # Load Excel
    df = pd.read_excel(excel_path)

    # Filter only invalid ones
    invalids = df[df['Status'].str.lower() == 'invalid'][['Xpath', 'Alternative Xpath']]

    # Helper: replace inside one file
    def process_file(file_path):
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in [".txt", ".properties", ".py", ".java"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            updated = False
            for _, row in invalids.iterrows():
                old_xpath, new_xpath = str(row['Xpath']), str(row['Alternative Xpath'])
                if old_xpath in content:
                    content = content.replace(old_xpath, new_xpath)
                    updated = True

            if updated:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ Updated: {file_path}")
            else:
                print(f"ℹ️ No invalid xpaths found in: {file_path}")

        elif file_ext == ".xlsx":
            tdf = pd.read_excel(file_path)
            updated = False
            for _, row in invalids.iterrows():
                old_xpath, new_xpath = str(row['Xpath']), str(row['Alternative Xpath'])
                if tdf.replace(old_xpath, new_xpath, inplace=True):
                    updated = True
            if updated:
                tdf.to_excel(file_path, index=False)
                print(f"✅ Updated Excel: {file_path}")
            else:
                print(f"ℹ️ No invalid xpaths found in Excel: {file_path}")
        else:
            print(f"❌ Unsupported file type: {file_path}")

    # Case 1: OR file given
    if target_file and os.path.exists(target_file):
        print(f"🔎 Processing Object Repository file: {target_file}")
        process_file(target_file)

    # Case 2: Process all files inside page folder
    elif page_folder and os.path.isdir(page_folder):
        print(f"🔎 Scanning folder: {page_folder}")
        for root, _, files in os.walk(page_folder):
            for file in files:
                if file.endswith((".txt", ".properties", ".py", ".java", ".xlsx")):
                    process_file(os.path.join(root, file))
    else:
        print("❌ Provide either a valid OR file or a page folder.")

if __name__ == "__main__":
    asyncio.run(main())
    subprocess.run(['node', SCRIPT_PATH], check=True)
    print(f"✅ Playwright script executed successfully. Output saved to: {SCRIPT_PATH}")
    xpath_file_path =r"D:\Self_healing_web_application\generated_xpath_details\xpath_details.json"
    dom_file_path =r"D:\Self_healing_web_application\output\sauce_demo\output\sauce_demo\all_page_dom_details.json"
    with open(xpath_file_path, 'r', encoding='utf-8') as f:
        xpath_content = f.read()
 
    xpath_content_all=read_json_file(xpath_file_path)
    dom_content_all=read_json_file(dom_file_path)
    xpath_content_dict = normalize_content(xpath_content_all, details_key="xpath_details")
    dom_content_dict = normalize_content(dom_content_all, details_key="dom_details")
    
    print("DEBUG - XPATH dict keys:", xpath_content_dict.keys())
    print("DEBUG - DOM dict keys:", dom_content_dict.keys())
    #page_mapping = match_xpath_and_dom(xpath_content_all, dom_content_all)
    response =[]
    for xpath_page, xpath_details in xpath_content_dict.items():
        found_match = False
        for dom_page, dom_details in dom_content_dict.items():
        # Partial match check
            if has_partial_word_match(xpath_page, dom_page):
                response.append(compare_xpathdetails_dom(xpath_details, dom_details))
                found_match = True
                break   # stop once match is found

        if not found_match:
            print(f"No DOM match found for {xpath_page}")
  
    # for page_name, details in page_mapping.items():
    #     xpath_details = details["xpath_details"]
    #     dom_details_list = details["dom_details_list"]

    #     if dom_details_list:
    #         for dom_details in dom_details_list:
    #             response.append(compare_xpathdetails_dom(xpath_details, dom_details))
    #     else:
    #         print(f"No DOM match found for {page_name}")

    print(response)
    save_ai_response_to_excel(response)
    excel_path=r"D:\Self_healing_web_application\validated_xpath\validated_xpath.xlsx"
    page_folder=r"D:\Self_healing_input\Pages"
    replace_invalid_xpaths(excel_path, target_file=None,page_folder=page_folder)
        