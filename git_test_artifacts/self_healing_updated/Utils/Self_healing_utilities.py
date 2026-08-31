import os
import re
import json
import asyncio
import subprocess
import difflib
import pandas as pd
from io import StringIO
from urllib.parse import urlparse
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from src.mcp_use_client import start_mcp_client, execute_mcp_use, close_mcp_client
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

# ─── Paths ────────────────────────────────────────────────────────────────────
current_path = os.getcwd()
output_folder            = os.path.join(current_path, "output")
output_script            = os.path.join(output_folder, "Dom_script")
output_dom               = os.path.join(output_folder, "Dom_details")
output_xpath_validate    = os.path.join(output_folder, "validated_xpath")
output_generate_xpath    = os.path.join(current_path,  "generated_xpath_details")
Action_collection        = os.path.join(output_folder, "Action_collection")
xpath_file_path          = os.path.join(output_generate_xpath, "xpath_details.json")
dom_file_path            = os.path.join(output_dom, "all_page_dom_details.json")

for p in [output_folder, output_script, output_dom, output_xpath_validate,
          output_generate_xpath, Action_collection]:
    os.makedirs(p, exist_ok=True)

SCRIPT_PATH           = os.path.join(output_script, "dom_collector.js")
SCRIPT_PATH_execution = os.path.join(output_script, "dom_collector_1.js")

api_key  = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"]  = api_key
os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint


# ─── Helpers ──────────────────────────────────────────────────────────────────
def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_mcp_prompt_compare(prompt_file, replace_dict=None):
    with open(prompt_file, 'r', encoding='utf-8') as f:
        template = f.read()
    if replace_dict:
        for key, value in replace_dict.items():
            if not isinstance(value, str):
                value = json.dumps(value)
            template = template.replace(key, value)
    return template


async def run_mcp_prompt(prompt_file, replace_dict=None):
    prompt = run_mcp_prompt_compare(prompt_file, replace_dict)
    return await execute_mcp_use(prompt)


# ─── Page extraction from action file ─────────────────────────────────────────
def extract_pages_from_action_file(action_source):
    """
    Extract ordered unique pages (name + URL) from an action file.

    Accepts:
      - str path to a .txt action file  (Page: [url] format)
      - list of action dicts            (JSON recorded actions)
      - str content of a .txt file

    Returns: [{"page_name": str, "url": str}, ...]
    """
    pages = []
    seen_urls = set()

    def _add(url):
        if url and url not in seen_urls:
            seen_urls.add(url)
            path = urlparse(url).path.strip("/")
            page_name = re.sub(r'[^a-zA-Z0-9]', '_', path) or "home"
            pages.append({"page_name": page_name, "url": url})

    if isinstance(action_source, list):
        # Raw JSON actions list
        for act in action_source:
            _add(act.get("url", ""))
    elif isinstance(action_source, str):
        if os.path.exists(action_source):
            with open(action_source, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = action_source
        for line in content.splitlines():
            m = re.match(r'Page:\s*\[(.+?)\]', line.strip())
            if m:
                _add(m.group(1))

    return pages


# ─── MCP: action file → Playwright DOM collector (no feature file step) ───────
async def main_from_actions(action_file_path):
    """
    Generate a Playwright DOM-collector script directly from the action file.
    Bypasses the Gherkin feature file step entirely.
    """
    print("Starting MCP client...")
    await start_mcp_client()

    pages = extract_pages_from_action_file(action_file_path)
    nav_data = json.dumps(pages, indent=2)

    # Read full action content for context
    with open(action_file_path, 'r', encoding='utf-8') as f:
        action_content = f.read()

    print("Generating Playwright DOM collector script from action file...")
    script_text = await run_mcp_prompt(
        'input/mcp_dom_collector_prompt.txt',
        {
            '{nav_data}': nav_data,
            '{action_content}': action_content
        }
    )

    close_mcp_client()
    print("MCP client closed.")

    with open(SCRIPT_PATH, 'w', encoding='utf-8') as f:
        clean = script_text.strip()
        if clean.startswith("```"):
            clean = "\n".join(
                line for line in clean.splitlines()
                if not line.strip().startswith("```")
            )
        f.write(clean)
    print(f"✅ Playwright DOM collector saved to: {SCRIPT_PATH}")


# ─── XPath validation via LLM ─────────────────────────────────────────────────
def compare_xpathdetails_dom(xpath_content, dom_content):
    """Ask LLM to validate each XPath against the page DOM and suggest alternatives."""
    model = AzureChatOpenAI(openai_api_version="2023-05-15", azure_deployment="qepracticekey")
    prompt = run_mcp_prompt_compare(
        'input/validte_xpath.txt',
        {
            '{dom_content}': dom_content,
            '{xpath_content}': xpath_content
        }
    )
    return model.invoke([HumanMessage(content=prompt)]).content.strip()


# ─── XPath re-verification against DOM (programmatic, no LLM) ─────────────────
def verify_xpath_in_dom(xpath_str, dom_html):
    """
    Programmatically check if an XPath exists in the given HTML DOM.
    Returns (found: bool, match_count: int).
    Uses lxml for accurate evaluation.
    """
    try:
        from lxml import html as lxml_html
        tree = lxml_html.fromstring(dom_html)
        results = tree.xpath(xpath_str)
        return len(results) > 0, len(results)
    except Exception as e:
        print(f"⚠️ XPath verify error for '{xpath_str}': {e}")
        return False, 0


def verify_alternative_xpaths(excel_path, dom_content_dict):
    """
    For every 'invalid' row in the Excel that has an alternative XPath,
    programmatically verify the alternative against the collected DOM.
    Adds 'Verified' and 'Match Count' columns and saves back to Excel.
    """
    df = pd.read_excel(excel_path)

    verified_col   = []
    match_cnt_col  = []

    for _, row in df.iterrows():
        status    = str(row.get("Status", "")).strip().lower()
        alt_xpath = str(row.get("Alternative Xpath", "")).strip()
        page      = str(row.get("Page", "")).strip()

        if status == "invalid" and alt_xpath and alt_xpath.lower() not in ("nan", "none", ""):
            # Find matching DOM for this page
            dom_html = None
            for dom_page, dom_details in dom_content_dict.items():
                if has_partial_word_match(page, dom_page):
                    dom_entry = dom_details.get("dom_details", dom_details)
                    dom_html  = dom_entry.get("html", "") if isinstance(dom_entry, dict) else ""
                    break

            if dom_html:
                found, count = verify_xpath_in_dom(alt_xpath, dom_html)
                verified_col.append("Yes" if found else "No")
                match_cnt_col.append(count)
            else:
                verified_col.append("DOM not found")
                match_cnt_col.append(0)
        else:
            verified_col.append("N/A")
            match_cnt_col.append(0)

    df["Verified"] = verified_col
    df["Match Count"] = match_cnt_col
    df.to_excel(excel_path, index=False)
    print(f"✅ Alternative XPath verification complete: {excel_path}")
    return df


# ─── Excel save ───────────────────────────────────────────────────────────────
def save_ai_response_to_excel(ai_response_list,
                               output_folder=output_xpath_validate,
                               file_name="validated_xpath.xlsx"):
    output_path = os.path.join(output_folder, file_name)
    all_dfs = []

    for response in ai_response_list:
        if not isinstance(response, str):
            continue
        clean_text = re.sub(r"```[a-zA-Z]*", "", response).replace("```", "").strip()
        if "|" not in clean_text or "---" not in clean_text:
            continue
        try:
            df = pd.read_csv(StringIO(clean_text), sep="|", engine="python")
            df = df.dropna(axis=1, how="all")
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            if len(df) > 0:
                all_dfs.append(df)
        except Exception as e:
            print(f"⚠️ Skipped invalid table: {e}")

    if not all_dfs:
        print("❌ No valid tables found in AI response.")
        return

    final_df = pd.concat(all_dfs, ignore_index=True)
    rename_map = {
        "page":              "Page",
        "xpath":             "Xpath",
        "status":            "Status",
        "alternative_xpath": "Alternative Xpath",
    }
    final_df.rename(columns=rename_map, inplace=True)
    final_df.to_excel(output_path, index=False, sheet_name="Validated_XPaths")
    print(f"✅ Saved {len(final_df)} rows to {output_path}")
    return final_df


# ─── Page name matching ────────────────────────────────────────────────────────
def normalize_name(name: str) -> str:
    return name.lower().replace("_page", "").replace("page", "").strip()


def has_partial_word_match(name1, name2, skip_words=None):
    if skip_words is None:
        skip_words = {"page"}
    words1 = [w for w in re.split(r'[_\W]+', name1.lower()) if w and w not in skip_words]
    words2 = [w for w in re.split(r'[_\W]+', name2.lower()) if w and w not in skip_words]
    return any(w1 in words2 or w2 in words1 for w1 in words1 for w2 in words2)


def normalize_content(content, details_key=None):
    normalized = {}
    if isinstance(content, dict):
        for page_name, details in content.items():
            normalized[page_name] = {details_key: details} if details_key else details
    elif isinstance(content, list):
        for entry in content:
            page_name = entry.get("page_name")
            if not page_name:
                continue
            normalized[page_name] = {details_key: entry} if details_key else entry
    else:
        raise TypeError("Unsupported content type for normalization")
    return normalized


# ─── Replace invalid XPaths in local files ────────────────────────────────────
def replace_invalid_xpaths(excel_path, target_file=None, page_folder=None,
                             approved_xpaths=None):
    """
    Replace invalid XPaths in local page files.

    approved_xpaths: optional set/list of old XPath strings that the user approved.
                     If None, all invalid rows are replaced.
    """
    df = pd.read_excel(excel_path)
    invalids = df[df['Status'].str.lower() == 'invalid'][['Xpath', 'Alternative Xpath']].dropna()

    replacements = [
        (str(r['Xpath']).strip(), str(r['Alternative Xpath']).strip())
        for _, r in invalids.iterrows()
        if approved_xpaths is None or str(r['Xpath']).strip() in approved_xpaths
    ]

    if not replacements:
        print("ℹ️ No approved replacements to apply.")
        return

    def process_file(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".py", ".txt", ".properties", ".java"]:
            return
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        updated = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                print(f"🔄 Replaced in {file_path}: {old} → {new}")
                updated = True
        if updated:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")

    if target_file and os.path.exists(target_file):
        process_file(target_file)
    elif page_folder and os.path.isdir(page_folder):
        for root, _, files in os.walk(page_folder):
            for file in files:
                if file.endswith((".py", ".txt", ".properties", ".java")):
                    process_file(os.path.join(root, file))
    else:
        print("❌ Provide either a valid OR file or page folder.")
