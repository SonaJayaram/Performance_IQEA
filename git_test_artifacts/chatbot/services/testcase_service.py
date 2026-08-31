"""Test Case Generation flow — headless backend.

Wraps the same utils the E2E Test Case panel uses. Sources: recorded flow
(screenshots + action file) and document (later). Generation via
generate_* + generate_testcases_with_dynamic_stop; save to a single-sheet Excel.
"""
import os

import utilities.Utilities_Xpath as utils

_OUT = os.path.join(os.getcwd(), "output")
TEST_CASE_COLLECTION = os.path.join(_OUT, "Test_Cases_collection")
SCREENSHOT_FOLDER = os.path.join(_OUT, "Action_collection", "Sauce_demo")


# -- document source -------------------------------------------------------
def extract_document(uploaded_file, filename):
    """Extract raw text from an uploaded PDF/DOCX/XLSX/TXT."""
    return utils.extract_text_from_document(uploaded_file, filename)


def from_document(extracted_data, image_data=None, navigation=None):
    """Generate test cases from document text. Returns the markdown response."""
    prompt = utils.generate_excel_testcases_with_document(
        "Test_case_generation_document", extracted_data, image_data, navigation)
    return utils.generate_testcases_with_dynamic_stop(prompt, 120, 5)


# -- recorded source -------------------------------------------------------
def read_action_file(path):
    """Read a saved recording's action file text (empty string if missing)."""
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def save_uploaded_images(files):
    """Persist uploaded images into the screenshot folder; return their filenames."""
    os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)
    names = []
    for f in files or []:
        dest = os.path.join(SCREENSHOT_FOLDER, f.name)
        with open(dest, "wb") as out:
            out.write(f.getbuffer())
        names.append(f.name)
    return names


def ocr_images(filenames):
    """OCR the given screenshot filenames and return a concise, summarised context."""
    import pytesseract
    from PIL import Image

    raw = ""
    for name in filenames:
        path = os.path.join(SCREENSHOT_FOLDER, name)
        if not os.path.exists(path):
            continue
        try:
            text = pytesseract.image_to_string(Image.open(path))
            raw += f"\nImage: {name}\nExtracted Text: {text.strip() or 'No text found'}\n"
        except Exception as e:
            raw += f"\nImage: {name}\nExtracted Text: (error: {e})\n"

    if not raw.strip():
        return ""
    summary_prompt = (
        "Summarize the following context into a concise and structured format "
        "(under 100 lines), preserving key actions, entities, and sequences for "
        f"test case generation. Avoid repetition. Context: {raw}"
    )
    return utils.get_queries_from_ai_updated(summary_prompt) or raw


def from_recorded(navigation, image_data, action_data, requirements):
    """Generate test cases from recorded screenshots + actions."""
    prompt = utils.generate_pom_from_excel_testcases(
        "Test_case_generation", navigation, image_data, action_data or None, requirements)
    return utils.generate_testcases_with_dynamic_stop(prompt, 15, 5)


# -- gap analysis + targeted generation (TMT knowledge base) ---------------
def gap_analysis(existing_tcs, action_data, image_data, requirements):
    """Compare against existing TMT test cases → {new, update, skip}."""
    return utils.analyze_testcase_gaps(existing_tcs, action_data, image_data, requirements)


def generate_targeted(scenarios, action_data, image_data, requirements):
    """Generate exactly the missing scenarios found by gap analysis."""
    if not scenarios:
        return ""
    return utils.generate_targeted_testcases(scenarios, action_data, image_data, requirements) or ""


def generate_replacement(title, reason, action_data, image_data, requirements):
    """Generate a replacement for an existing test case flagged for update."""
    return utils.generate_replacement_testcase(title, reason, action_data, image_data, requirements) or ""


def push_to_azure(response, parent_id=None):
    """Create individual Azure DevOps Test Case work items from a markdown response.
    Returns {'created': [ids], 'errors': [msgs]}."""
    from utilities.TMT_Connection import Test_management_tool_utils as tmt_utils

    rows = utils.parse_testcases_from_markdown(response)
    groups, current = {}, None
    for row in rows:
        name = (row.get("name") or "").strip()
        if name:
            current = name
            groups[current] = []
        if current:
            groups[current].append(row)

    created, errors = [], []
    for title, trows in groups.items():
        try:
            wid = tmt_utils.create_testcase_with_steps(
                title=title, steps_xml=tmt_utils.build_steps_xml(trows), parent_id=parent_id)
            (created if wid else errors).append(wid or f"Failed: {title}")
        except Exception as e:
            errors.append(f"{title}: {e}")
    return {"created": created, "errors": errors}


# -- category summary ------------------------------------------------------
def category_counts(response):
    """Count distinct test cases per category (mirrors the panel's category view).
    Returns an ordered dict-like list of (category, count) plus total."""
    from collections import defaultdict
    rows = utils.parse_testcases_from_markdown(response)
    buckets = defaultdict(list)
    for row in rows:
        name = (row.get("name") or "").strip()
        if not name:            # rows 2+ of a TC have blanked names
            continue
        cat = (row.get("category") or "").strip().lower() or "others"
        if name not in buckets[cat]:
            buckets[cat].append(name)
    counts = {cat: len(names) for cat, names in buckets.items()}
    return counts, sum(counts.values())


# -- persist ---------------------------------------------------------------
def save_testcases(response):
    """Persist generated cases to a single-sheet Excel. Returns the file path."""
    os.makedirs(TEST_CASE_COLLECTION, exist_ok=True)
    return utils.covert_response_to_testcases_single_sheet(response, TEST_CASE_COLLECTION)
