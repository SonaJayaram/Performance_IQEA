import random
import re
import string
import uuid
from io import StringIO
import pandas as pd
from datetime import datetime
import PyPDF2
from docx2txt import docx2txt
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
import os
import time
#############
conversation_prompt_template ="""
You are an expert AI prompt engineer specializing in creating realistic, logically connected **multi-turn conversation prompts** to evaluate an LLM’s reasoning depth.

---
### Input
**Functional Requirement Text:**
{requirements}

**Category:**
{category}

**Subcategory:**
{subcategory}

---
### Objective
Generate a conversation that simulates a **natural, progressive dialogue** between a human evaluator and an LLM.  
Each follow-up question **must logically depend** on the previous **answer**, exploring deeper nuances or implications of that answer.

---
### Rules
1. Start with a **broad introductory question** directly tied to the requirement.
2. After each answer, imagine how a human would naturally ask a **follow-up** question that digs deeper into:
   - A term or concept mentioned in the LLM’s previous answer.
   - A scenario, limitation, or implication raised by the previous response.
3. Maintain **strong contextual continuity** — every question should make sense only if the previous answer existed.
4. Include exactly **5 rounds** of Q&A.
5. Provide the output strictly as a Markdown table with columns:

| Category | Subcategory | Conversation Step | Question | Assumed LLM Answer |

6. Ensure:
   - Step 1 introduces the topic clearly.
   - Step 2 clarifies or explores a detail from Step 1’s answer.
   - Step 3 compares or challenges a concept from Step 2.
   - Step 4 deepens with an exception, risk, or limitation.
   - Step 5 concludes with a reflective or strategic insight.
7. Maintain **realistic conversational flow** — avoid topic jumps.
8. Keep responses short but rich in explanation.
9. Do not include meta text, notes, or explanations outside the table.

---
### Example Format

| Conversation Step | Question | Assumed LLM Answer |
|------------------|-----------|--------------------|
| 1 | Can you explain the primary difference between comprehensive major medical plans and critical illness plans? | Comprehensive plans pay providers for actual medical expenses; critical illness plans pay a fixed cash amount upon diagnosis. |
| 2 | Since the cash benefit isn’t linked to bills, how do people usually use it? | Typically to cover lost income or non-medical expenses like rent or travel for treatment. |
| 3 | So, would someone benefit from having both types of plans? | Yes, they are complementary—one covers medical costs, the other helps with financial gaps. |
| 4 | You mentioned “pre-defined illnesses.” What happens if an illness isn’t on that list? | The plan won’t pay; coverage is restricted to explicitly listed conditions. |
| 5 | Given those restrictions, how does underwriting differ from major medical plans? | Critical illness plans involve full medical underwriting, unlike guaranteed-issue comprehensive plans. |

---
### Task
Based on the input requirement, generate a **contextually coherent 5-turn conversation** following the above pattern.
"""

prompt_template = """You are an expert Prompt Engineer tasked with generating **validation question prompts** to thoroughly test an LLM chatbot that has been fed the provided requirement document(s).

OBJECTIVE:
For the given **Category** and **Subcategory** (extracted from the requirements), generate a comprehensive, diverse set of user-style questions that another team can feed to the LLM to validate its knowledge, behavior, robustness, and boundaries. Your job is to produce many realistic variations across multiple question types so the LLM can be validated in all possible ways.

--- 
### Input (placeholders)
**Functional Requirement Text:**  
{requirements}

**Category:**  
{category}

**Subcategory:**  
{subcategory}

(Optional) **Additional context / examples:**  
{context}

--- 
### Question Types (must be covered — produce variations for each)
- Comparisons
- Scenario Based
- Compute for X
- Dynamic Info
- Factual
- Client-related
- Investment Advice
- Not Personal Finance
- Outside Knowledge Base

--- 
### Strict Instructions (Behavioral rules)
1. **Understand first:** Fully read the `requirements` and build a clear mental model of the feature, domain, and constraints before generating questions. Use any named entities, constraints, thresholds, or example scenarios found in the requirements to make questions realistic and contextual.
2. **One row per question:** Return each generated question as one row in the required Markdown table (see Output Format).
3. **Diversity & variations:** For each Question Type above generate **multiple distinct variations** (paraphrases, short/long forms, formal/informal tone) — at least **5 unique questions per Question Type**, unless the type is clearly irrelevant to the given Category/Subcategory (if irrelevant, output zero rows for that type but list the reason in the internal rationale — do NOT output the rationale in the final table).
4. **Multi-turn & follow-ups:** For at least some scenario-based and factual questions, include follow-up questions that a user might ask after receiving an LLM response (format each follow-up as a separate question row).
5. **Out-of-scope checks:** Produce explicit out-of-scope questions (e.g., requests requiring PHI/external APIs/real-time location) that should cause the LLM to refuse politely or indicate it lacks that data.
6. **Ambiguity & traps:** Include ambiguous or intentionally misleading phrasings to verify the LLM asks clarifying questions rather than hallucinating answers.
7. **Compute & numeric verification:** For "Compute/Quantify" type, generate questions that require simple arithmetic or threshold checks using values from requirements (or realistic sample values if none exist).
8. **Localization & units:** Provide regional/unit variations (e.g., metric vs imperial, currency formats) where applicable.
9. **Tone & role variations:** Include prompts phrased as end-users, domain experts, auditors, and casual users to test differing expectations.
10. **Safety & policy checks:** Add a few prompts that test model's handling of sensitive, illegal, or disallowed requests—these should be labeled as Out-of-scope or Safety checks.
11. **Answer expectation hints (internal only):** Do not include this in the output table — but generate questions that clearly reveal if the LLM's reply is correct or not (e.g., ask for a specific field or value found in the requirements).
12. **No explanations in output:** The final output must contain only the Markdown table rows — no extra commentary, no diagnostics, no internal rationale, and no code fences.

--- 
### Output Format (STRICT — no extra text)
Return **only** a Markdown table with EXACT columns and header below (no prelude, no trailing text):

| Question Type | Category | Subcategory | Question |Assumed LLM Answer |
|---------------|----------|-------------|----------|--------------------|
| <Question Type> | <Category> | <SubCategory> | <Full user question text> |<Full answer text> |
| ... | ... | ... | ... |... |

- Each cell must be a plain string.  
- Preserve punctuation and quotation marks inside the Question cell.  
- Do not output additional columns.  
- If a question contains multiple parts, keep them in the same Question cell separated by a newline or semicolon.

--- 
### Example row (for reference only — do NOT include extra text outside the table):
| Comparisons | Vandalism | Weather Condition | What was the weather like during the incident? Describe the road condition. |

--- 
### Task
Using the `requirements`, `category`, and `subcategory` create a **large, diverse list** of question prompts (as specified above). Output them strictly in the Markdown table format requested. Begin now.
"""

###################
category_prompt = """
You are an expert business analyst specializing in requirement classification.

You are given a document containing system or process requirements.

Your task:
1. Carefully read the provided requirements text.
2. Identify the **main functional areas** or **themes** — these are the **Categories**.
3. For each Category, identify 2–4 **specific topics or aspects** within it — these are the **Subcategories**.
4. Do not invent unrelated categories. Ensure that every category and subcategory is derived from the actual requirement content.

Output format (very important):
Provide the result strictly as a Markdown table with the headers:
| Category | Subcategory |

Example output:
| Category | Subcategory |
|-----------|--------------|
| Demand Management | Planning |
| Demand Management | Variability |
| Forecasting | Accuracy |
| Forecasting | Methods |
| Inventory Management | Levels |
| Inventory Management | Optimization |

Guidelines:
- Keep category names concise (2–4 words).
- Avoid repetition.
- Focus on logical grouping (e.g., if requirements mention demand forecasting, production scheduling, supplier lead time, treat those as separate categories).
- Include at least 5–10 total category–subcategory pairs.
- Do not include explanations, reasoning, or extra text outside the Markdown table.

Now extract the Category and Subcategory pairs from the following requirements:

{requirements}

"""



def read_category_subcategory_from_excel(excel_path):
    """
    Reads Category and Subcategory pairs from Excel.
    Returns a list of tuples: [(Category, Subcategory), ...]
    """
    try:
        df = pd.read_excel(excel_path)
        if not {"Category", "Subcategory"}.issubset(df.columns):
            raise ValueError("Excel file must have 'Category' and 'Subcategory' columns.")

        pairs = []
        for _, row in df.iterrows():
            category = str(row["Category"]).strip()
            subcategory = str(row["Subcategory"]).strip()
            if category and subcategory:
                pairs.append((category, subcategory))
        return pairs

    except Exception as e:
        print(f"❌ Error reading category/subcategory Excel: {e}")
        return []


def extract_text_from_document(file_path):
    text = ""

    filename = os.path.basename(file_path).lower()

    try:
        if filename.endswith(".pdf"):
            # --- PDF Extraction ---
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += re.sub(r'\W+', ' ', extracted)

        elif filename.endswith(".docx"):
            # --- Word Document Extraction ---
            text_content = docx2txt.process(file_path)
            text += re.sub(r'\W+', ' ', text_content)

        elif filename.endswith(".txt"):
            # --- Plain Text File Extraction ---
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()
                text += re.sub(r'\W+', ' ', text_content)

        elif filename.endswith((".xlsx", ".xls")):
            # --- Excel Extraction (iterate all sheets & cells) ---
            df_dict = pd.read_excel(file_path, sheet_name=None)
            for sheet_name, df in df_dict.items():
                for col in df.columns:
                    for cell in df[col]:
                        if pd.notna(cell):
                            text += re.sub(r'\W+', ' ', str(cell)) + " "
        else:
            print(f"⚠️ Unsupported file type: {filename}")
            return ""

    except Exception as e:
        print(f"❌ Error extracting text from {filename}: {e}")

    print("✅ Extracted text preview:", text[:300], "...")
    return text

def load_prompt_from_file(prompt_type):


    if prompt_type == "category_subcatregory_geenration":
        return category_prompt
    elif prompt_type== "prompt_generation":
        return prompt_template
    elif prompt_type== "conversation_prompt":
        return conversation_prompt_template
    else:
        raise ValueError(f"Invalid prompt type: {prompt_type}")

    with open(prompt_file, "r", encoding="utf-8") as file:
        template = file.read()
    print("-------------file- prompttemplate--------------")
    return template
def generate_category_prompt(prompt_type,requirements=""):
    prompt_template = load_prompt_from_file(prompt_type)
    # Conditionally inject Action Data section or leave it blank
    final_prompt = prompt_template.format(requirements=requirements)
    print(final_prompt)
    return final_prompt


def parse_category_subcategory_from_response(llm_response):
    """
    Parse LLM response containing markdown-formatted Category–Subcategory table.
    Handles code fences, markdown headers, empty lines, and extra characters.

    Returns:
        list of tuples -> [(Category, Subcategory), ...]
    """

    if not llm_response or not isinstance(llm_response, str):
        print("⚠️ Invalid LLM response input.")
        return []

    # --- Step 1: Remove markdown code fences like ```markdown or ```
    cleaned_text = re.sub(r"```(?:markdown)?", "", llm_response, flags=re.IGNORECASE).strip()

    # --- Step 2: Find the markdown table section (lines with | delimiters)
    table_lines = [line.strip() for line in cleaned_text.splitlines() if "|" in line]
    if not table_lines:
        print("⚠️ No markdown table found in response.")
        return []

    # --- Step 3: Remove the header separator (----) and empty lines
    table_lines = [line for line in table_lines if not re.match(r"^\s*\|?\s*-+\s*\|", line)]

    # --- Step 4: Extract data rows (skip the header)
    data_rows = []
    for line in table_lines[1:]:  # skip header row
        parts = [col.strip() for col in line.strip("|").split("|")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            data_rows.append((parts[0], parts[1]))

    # --- Step 5: Remove duplicates and empty values
    unique_rows = list({(cat, sub): None for cat, sub in data_rows if cat and sub}.keys())

    if not unique_rows:
        print("⚠️ No valid category–subcategory pairs found after parsing.")
        return []

    # Optional: print preview for debug
    print(f"✅ Parsed {len(unique_rows)} category–subcategory pairs successfully.")
    return unique_rows

def generate_prompt(prompt_type,category,subcategory,requirements,context=None):
    prompt_template = load_prompt_from_file(prompt_type)
    # Conditionally inject Action Data section or leave it blank
    final_prompt = prompt_template.format(category=category,subcategory=subcategory,requirements=requirements,context=None)
    print(final_prompt)
    return final_prompt
def parse_prompts_from_markdown_backup(response_text):
    """
    Parse generated prompts into structured list.
    Expected format: each prompt is a sentence or paragraph.
    """
    prompts = []
    lines = [line.strip() for line in response_text.split("\n") if line.strip()]
    for i, line in enumerate(lines, start=1):
        prompts.append({
            "Prompt Description": f"Generated Prompt {i}",
            "Prompt": line
        })
    return prompts
def generate_prompts_with_dynamic_stop_backup(constructed_prompt, max_prompts,
                                       min_new_threshold, max_attempts=50):
    """
    Dynamically generate prompts for a given category/subcategory,
    stopping when few new prompts are added.
    """

    all_prompts = []
    seen_descriptions = set()
    all_raw_responses = ""
    attempt = 0

    while attempt < max_attempts:
        print(f"*********** Iteration {attempt + 1} ***********")

        # --- Add exclusion list to the prompt ---
        if all_prompts:
            existing_desc = set(p["Prompt Description"] for p in all_prompts)
            exclusion_text = (
                "Already generated prompts:\n" + "\n".join(existing_desc) +
                "\nNow generate NEW unique prompts not in the above list."
            )
            prompt = constructed_prompt + "\n\n" + exclusion_text
        else:
            prompt = constructed_prompt

        try:
            response = get_queries_from_ai_updated(prompt)
            all_raw_responses += "\n" + response

            try:
                new_prompts = parse_prompts_from_markdown(response)
            except Exception as parse_err:
                print(f"⚠️ Parsing error: {parse_err}. Skipping this response.")
                attempt += 1
                continue

            new_added = 0
            for pr in new_prompts:
                key = pr["Prompt"].strip().lower()
                if key not in seen_descriptions:
                    seen_descriptions.add(key)
                    all_prompts.append(pr)
                    new_added += 1

            print(f"New unique prompts added: {new_added} | Total: {len(all_prompts)}")

            # --- Stop Conditions ---
            if new_added < min_new_threshold:
                print(f"✅ Stopping: Less than {min_new_threshold} new prompts generated.")
                break
            if len(all_prompts) >= max_prompts:
                print(f"✅ Stopping: Reached max_prompts limit ({max_prompts}).")
                break

        except Exception as e:
            print(f"⚠️ Exception during AI call: {e}. Skipping iteration.")
            attempt += 1
            continue

        attempt += 1

    return all_prompts

def parse_prompts_from_markdown(response_text):
    """
    Parse a Markdown table with columns:
    | Question Type | Category | Subcategory | Question |
    Returns a list of dicts with keys exactly:
      "Question Type", "Category", "Subcategory", "Question"
    If parsing fails, returns [].
    """

    if not response_text or not isinstance(response_text, str):
        return []

    text = response_text.strip()

    # Remove surrounding code fences if present
    if text.startswith("```") and text.endswith("```"):
        text = "\n".join(line for line in text.splitlines() if not line.strip().startswith("```"))

    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]

    # Find header line index that contains the expected headers (case-insensitive)
    header_idx = None
    for i, ln in enumerate(lines):
        lower = ln.lower()
        if "question" in lower and "category" in lower and "subcategory" in lower:
            header_idx = i
            break

    if header_idx is None:
        # try a looser detection: look for a pipe-containing line with at least 3 columns
        for i, ln in enumerate(lines):
            if "|" in ln and ln.count("|") >= 3:
                header_idx = i
                break

    if header_idx is None:
        return []

    # collect table lines from header_idx until a non-table block or heading occurs
    table_lines = []
    for ln in lines[header_idx:]:
        # stop when next markdown section heading starts (e.g., "#### ..." or "# ")
        if re.match(r'^\s*#{1,6}\s+', ln):
            break
        # accept lines containing '|' as part of table
        if "|" in ln:
            table_lines.append(ln)
        else:
            # treat a non-pipe line as break point
            break

    if not table_lines or len(table_lines) < 2:
        return []

    # Normalize lines: ensure leading/trailing pipe so pandas reads columns consistently
    normalized = []
    for ln in table_lines:
        s = ln.strip()
        if not s.startswith("|"):
            s = "| " + s
        if not s.endswith("|"):
            s = s + " |"
        normalized.append(s)

    csv_text = "\n".join(normalized)

    # Use pandas to parse (safer than naive splitting)
    try:
        df = pd.read_csv(StringIO(csv_text), sep="|", engine="python", skipinitialspace=True, dtype=str, on_bad_lines='skip')
    except Exception:
        # fallback: naive split parsing
        rows = []
        header_parts = [h.strip() for h in re.split(r'\s*\|\s*', normalized[0].strip()) if h.strip()]
        for ln in normalized[1:]:
            parts = [p.strip() for p in re.split(r'\s*\|\s*', ln.strip()) if p.strip()]
            if len(parts) == len(header_parts):
                rows.append(dict(zip(header_parts, parts)))
        # Normalize keys to expected names
        results = []
        for r in rows:
            res = {
                "Question Type": r.get(next(k for k in r if "question" in k.lower()), "").strip(),
                "Category": r.get(next((k for k in r if "category" in k.lower()), ""), "").strip(),
                "Subcategory": r.get(next((k for k in r if "sub" in k.lower()), ""), "").strip(),
                "Question": r.get(next((k for k in r if "question" in k.lower()), ""), "").strip(),
            }
            results.append(res)
        return results

    # Clean DataFrame: drop fully empty columns, trim header names
    df = df.dropna(axis=1, how='all')
    df.columns = [str(c).strip() for c in df.columns]
    # Remove empty columns that pandas may add
    df = df.loc[:, [c for c in df.columns if str(c).strip() != ""]]

    # Normalize column names to canonical expected keys
    col_map = {}
    for col in df.columns:
        low = col.lower()
        if "question type" in low or (("question" in low) and ("type" in low)):
            col_map[col] = "Question Type"
        elif "category" in low:
            col_map[col] = "Category"
        elif "subcategory" in low or "sub category" in low:
            col_map[col] = "Subcategory"
        elif re.fullmatch(r'question', low) or 'prompt' in low:
            col_map[col] = "Question"
        else:
            # if unknown, try to map by position later
            col_map[col] = col

    df = df.rename(columns=col_map)

    # If required columns are missing but df has 4 cols, assign by position
    expected = ["Question Type", "Category", "Subcategory", "Question"]
    missing = [c for c in expected if c not in df.columns]
    if missing and df.shape[1] >= 4:
        # assign first 4 columns
        first4 = df.columns[:4]
        df = df.rename(columns={first4[0]: "Question Type", first4[1]: "Category", first4[2]: "Subcategory", first4[3]: "Question"})

    # Final filter: keep only expected columns (add empty if absent)
    for c in expected:
        if c not in df.columns:
            df[c] = ""

    # Trim whitespace and coerce to string
    for col in expected:
        df[col] = df[col].astype(str).map(lambda x: x.strip())

    # Build result list
    results = []
    for _, row in df[expected].iterrows():
        # Skip empty question rows
        if not row["Question"] or row["Question"].strip() == "":
            continue
        results.append({
            "Question Type": row["Question Type"],
            "Category": row["Category"],
            "Subcategory": row["Subcategory"],
            "Question": row["Question"]
        })

    return results


def generate_prompts_with_dynamic_stop(constructed_prompt, max_prompts,
                                       min_new_threshold, max_attempts=50,
                                       backoff_seconds=1.0):
    """
    Iteratively generate validation questions for a Category/Subcategory by calling the LLM.
    Returns: (all_questions_list, concatenated_raw_responses)

    all_questions_list: list of dicts with keys:
       "Question Type", "Category", "Subcategory", "Question"
    """

    all_questions = []
    seen_questions = set()
    all_raw_responses = ""
    attempt = 0

    while attempt < max_attempts:
        print(f"*********** Iteration {attempt + 1} ***********")

        # Build exclusion list (use Question text)
        if all_questions:
            print(all_questions)
            existing_qs = [q["Question"] for q in all_questions if q.get("Question")]
            print(existing_qs)
            # use short dedupe lines (one question per line)
            exclusion_text = "Already generated questions (do NOT repeat these):\n" + "\n".join(existing_qs) + \
                             "\nNow generate NEW unique questions not present in the above list."
            prompt_to_send = constructed_prompt + "\n\n" + exclusion_text
        else:
            prompt_to_send = constructed_prompt

        try:
            response = get_queries_from_ai_updated(prompt_to_send)
            if not response:
                print("⚠️ Empty response from LLM. Backing off and retrying...")
                time.sleep(backoff_seconds)
                attempt += 1
                continue

            all_raw_responses += "\n" + response

            # Parse response table into structured rows
            try:
                parsed = parse_prompts_from_markdown(response)
            except Exception as e:
                print(f"⚠️ Parser exception: {e}. Response preview:\n{response[:400]}")
                time.sleep(backoff_seconds)
                attempt += 1
                continue

            if not parsed:
                print("⚠️ No rows parsed from LLM response. Response preview:")
                print(response[:400])
                time.sleep(backoff_seconds)
                attempt += 1
                continue

            new_added = 0
            for row in parsed:
                q_text = (row.get("Question") or "").strip()
                if not q_text:
                    continue
                key = q_text.lower()
                if key not in seen_questions:
                    seen_questions.add(key)
                    all_questions.append(row)
                    new_added += 1

            print(f"New unique questions added: {new_added} | Total unique: {len(all_questions)}")

            # Stop conditions
            if new_added < min_new_threshold:
                print(f"✅ Stopping: less than {min_new_threshold} new questions generated this iteration.")
                break
            if len(all_questions) >= max_prompts:
                print(f"✅ Stopping: reached max_prompts limit ({max_prompts}).")
                break

            # small backoff to avoid rate limits
            time.sleep(backoff_seconds)

        except Exception as e:
            print(f"⚠️ Exception during LLM call or processing: {e}")
            time.sleep(backoff_seconds * 2)
            attempt += 1
            break

        attempt += 1

    return all_raw_responses
def generate_testcases_with_dynamic_stop_backup(constructed_prompt, max_testcases,
                                         min_new_threshold,max_attempts=50):
    """
    Generate test cases dynamically, stopping when new unique test cases are too few.

    Args:
        constructed_prompt (str): Base prompt.
        max_testcases (int): Safety cap to avoid infinite generation.
        max_attempts (int): Maximum AI calls allowed.
        min_new_threshold (int): Minimum new test cases required to continue generation.

    Returns:
        list: All unique test cases.
        str: Concatenated raw responses.
    """
    all_prompts = []
    seen_steps = set()
    all_raw_responses = ""
    attempt = 0

    while attempt < max_attempts:
        print(f"***********Iteration {attempt + 1}*****************")

        # Build exclusion prompt
        if all_prompts:
            existing_names = set(c["Prompt Description"] for c in all_prompts)
            exclusion_text = (
                    "Already generated test cases:\n" + "\n".join(existing_names) +
                    "\nNow generate NEW test cases not in the above list. Continue numbering."
            )
            prompt = constructed_prompt + "\n\n" + exclusion_text
        else:
            prompt = constructed_prompt


        try:
            response = get_queries_from_ai_updated(prompt)
            all_raw_responses += "\n" + response

            # Parse test cases
            try:
                new_cases = parse_testcases_from_markdown(response)
            except Exception as parse_err:
                print(f"⚠️ Parsing error: {parse_err}. Skipping this response.")
                attempt += 1
                continue
            new_added = 0
            for case in new_cases:
                # key = (case["name"], case["step_number"])
                key = case["Prompt Description"].strip().lower()
                if key not in seen_steps:
                    seen_steps.add(key)
                    all_prompts.append(case)
                    new_added += 1

            print(f"New unique test cases added: {new_added} | Total: {len(all_prompts)}")

            # Stop conditions
            if new_added < min_new_threshold:
                print(f"✅ Stopping: less than {min_new_threshold} new test cases generated.")
                break
            if len(all_prompts) >= max_testcases:
                print(f"✅ Stopping: reached max_testcases limit ({max_testcases}).")
                break
        except Exception as e:
            # Handle any AI or unexpected runtime exception
            print(f"⚠️ Exception during AI call or processing: {e}. Skipping this iteration.")
            # Optionally, you could also log it to a file
            attempt += 1
            continue
        attempt += 1

    return all_raw_responses
def cat_subcat_spilt(reponse):
    category =""
    subcategory=""
    return category,subcategory
def parse_and_display_testcases_categorywise(md_text):
    import streamlit as st
    import re
    from collections import defaultdict

    # --- Parse Markdown Table ---
    rows = []
    md_text = md_text.strip()
    lines = [line for line in md_text.splitlines() if line.strip() and not re.match(r'^\|\s*-', line)]
    buffer = ""

    for line in lines:
        if line.startswith("|"):
            buffer += line + "\n"
            if buffer.count("|") >= 8:  # expecting 7 columns
                parts = re.split(r'\s*\|\s*', buffer.strip())
                parts = [p.strip() for p in parts[1:-1]]
                if len(parts) == 7:
                    name = parts[0].strip().lower()
                    category = parts[6].strip().lower()
                    if name == "name" or category == "category" or not parts[0]:
                        buffer = ""
                        continue
                    rows.append({
                        "name": parts[0],
                        "step_number": parts[1],
                        "description": parts[2],
                        "expected": parts[3],
                        "status": parts[4],
                        "category": parts[6],
                    })
                buffer = ""

    # --- Group test cases by category ---
    category_to_cases = defaultdict(list)
    for row in rows:
        name = row["name"].strip()
        category = row["category"].strip().lower() if row["category"].strip() else "others"
        if name not in category_to_cases[category]:
            category_to_cases[category].append(name)

    category_counts = {cat: len(names) for cat, names in category_to_cases.items()}
    total = sum(category_counts.values())
    category_counts["total"] = total

    # --- Define colors ---
    color_map = {
        "positive": "#27ae60",
        "negative": "#e74c3c",
        "workflow": "#2980b9",
        "ui": "#f1c40f",
        "edge case": "#8e44ad",
        "others": "#95a5a6",
        "total": "#7f8c8d"
    }

    # --- Define category definitions ---
    category_meanings = {
        "positive": "Covers standard and expected user behavior ensuring the application works as intended.",
        "negative": "Tests invalid inputs or unexpected user actions to confirm the system handles errors gracefully.",
        "workflow": "Validates complete end-to-end business processes that span multiple functionalities.",
        "ui": "Ensures the user interface components (labels, buttons, alignment, responsiveness) meet design standards.",
        "edge case": "Focuses on extreme or boundary conditions that test the robustness and limits of the system.",
        "backend": "Validates APIs, data transformations, integrations, and server-side logic without UI involvement.",
        "performance": "Measures response time, scalability, and system stability under different load conditions.",
        "accessibility": "Ensures the application is usable by all users, including those with disabilities (WCAG compliance).",
        "others": "Represents miscellaneous or uncategorized test cases not fitting into other specific groups.",
        "total": "Sum of all test cases across categories."
    }

    # --- CSS styling ---
    st.markdown("""
        <style>
            .testcase-container {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 10px;
            }
            .testcase-box {
                width: 150px;
                height: 70px;
                border-radius: 10px;
                color: white;
                padding: 6px;
                text-align: center;
                position: relative;
                box-shadow: 1px 2px 6px rgba(0,0,0,0.15);
                transition: transform 0.2s ease-in-out;
                font-family: 'Segoe UI', sans-serif;
            }
            .testcase-box:hover { transform: scale(1.05); }
            .testcase-title { font-size: 13px; font-weight: 600; margin-bottom: 2px; }
            .testcase-count { font-size: 20px; font-weight: 700; margin: 0; }
            .tooltip {
                visibility: hidden;
                background-color: rgba(0, 0, 0, 0.85);
                color: #fff;
                text-align: left;
                padding: 6px;
                border-radius: 6px;
                position: absolute;
                z-index: 1;
                bottom: 110%;
                left: 50%;
                transform: translateX(-50%);
                width: 220px;
                font-size: 11px;
                line-height: 1.3;
            }
            .testcase-box:hover .tooltip { visibility: visible; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 🧾 Category-wise Test Case Summary")

    # --- Build category summary boxes ---
    boxes = []
    for cat, count in category_counts.items():
        color = color_map.get(cat, "#34495e")
        meaning = category_meanings.get(cat, "No description available.")
        box_html = (
            f"<div class='testcase-box' style='background-color:{color};'>"
            f"<div class='testcase-title'>{cat.capitalize()}</div>"
            f"<div class='testcase-count'>{count}</div>"
            f"<div class='tooltip'>{meaning}</div>"
            f"</div>"
        )
        boxes.append(box_html)

    html = "<div class='testcase-container'>" + "".join(boxes) + "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.write(" ")

    return category_counts
def get_queries_from_ai_updated(formatted_summary):
   try:
        model = AzureChatOpenAI(
            openai_api_version="2023-05-15",
            azure_deployment="qepracticekey",
            max_tokens=4000,  # adjust depending on your model quota
            temperature=0
        )
        message = HumanMessage(content=formatted_summary)
        output_value = model([message])
        print(output_value)
        return output_value.content
   except Exception as e:
        print(f"❌ Failed to parse markdown table: {e}")


def parse_testcases_from_markdown(md_text):
    """
    Parse a Markdown table into structured test case dicts.
    Handles multi-line cells and extra pipes in descriptions.
    Returns a list of dicts, each with test case name, step number, description, expected, status, type, category.
    """
    import re
    rows = []
    md_text = md_text.strip()

    # Remove header/separator lines
    lines = [line for line in md_text.splitlines() if line.strip() and not re.match(r'^\|\s*-', line)]

    buffer = ""
    for line in lines:
        if line.startswith("|"):
            buffer += line + "\n"
            # Count pipes in the line; a full row should have 8 '|' for 7 columns
            if buffer.count("|") >= 8:
                parts = re.split(r'\s*\|\s*', buffer.strip())
                parts = [p.strip() for p in parts[1:-1]]  # skip first and last empty split
                if len(parts) == 7:
                    rows.append({
                        "name": parts[0],
                        "step_number": parts[1],
                        "description": parts[2],
                        "expected": parts[3],
                        "status": parts[4],
                        "type": parts[5],
                        "category": parts[6],
                    })
                buffer = ""  # reset for next row

    return rows

def generate_random_prefix(length=8):
    """
        Returns a compact unique suffix based on timestamp (microseconds) + 6 hex chars from uuid.
        Example: 20251110_212845_123456_a1b2c3
        """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # includes microseconds
    rand = uuid.uuid4().hex[:6]
    return f"{ts}_{rand}"
# def clean_table_lines(markdown_text):
#     """Extracts all markdown table lines (even across multiple tables)."""
#     lines = markdown_text.splitlines()
#     table_lines = []
#     current_table = []
#
#     for line in lines:
#         if "|" in line.strip():  # part of a markdown table
#             current_table.append(line)
#         else:
#             if current_table:  # table ended, store it
#                 table_lines.extend(current_table)
#                 current_table = []
#
#     # capture the last table if markdown ends with one
#     if current_table:
#         table_lines.extend(current_table)
#
#     # remove empty lines and ensure alignment pipes exist
#     return [ln for ln in table_lines if ln.strip() and "|" in ln]


# def covert_response_to_testcases_single_sheet(markdown_text, test_collection, output_file="prompt_LLM_validator"+generate_random_prefix()+".xlsx"):
#     print("\n🚀 Starting test case parsing (Single Sheet Version)...")
#     # --- Normalize input ---
#     if isinstance(markdown_text, list):
#         markdown_text = "\n".join(str(line) for line in markdown_text)
#     elif not isinstance(markdown_text, str):
#         markdown_text = str(markdown_text)
#
#     # --- Remove code block wrapper ---
#     if markdown_text.startswith("```"):
#         markdown_text = "\n".join(
#             line for line in markdown_text.splitlines()
#             if not line.strip().startswith("```")
#         )
#
#     all_dfs = []
#
#     # --- Clean table lines ---
#     table_lines = clean_table_lines(markdown_text)
#
#     # ✅ Accept any markdown table (don’t depend on “Test Case Name”)
#     if len(table_lines) >= 2 and "|" in table_lines[0]:
#         try:
#             df = pd.read_csv(StringIO("\n".join(table_lines)), sep="|", engine="python", on_bad_lines="skip")
#             df = df.dropna(axis=1, how="all")
#             df.columns = [re.sub(r"\*+", "", col.strip()) for col in df.columns]
#             for col in df.select_dtypes(include="object").columns:
#                 df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
#             all_dfs.append(df)
#         except Exception as e:
#             print(f"❌ Failed to parse markdown table: {e}")
#
#     if not all_dfs:
#         print("⚠️ No valid table found to save.")
#         return
#
#     final_df = pd.concat(all_dfs, ignore_index=True)
#
#     # --- Save to Excel ---
#     if not os.path.exists(test_collection):
#         os.makedirs(test_collection)
#         print(f"📁 Created output directory: {test_collection}")
#
#     excel_path = os.path.join(test_collection, output_file)
#     final_df.to_excel(excel_path, index=False, sheet_name="All_Prompts")
#     print(f"✅ Saved all generated questions to: {excel_path}")
#     return output_file
def extract_text_from_document_streamlit(uploaded_file, filename):
    text = ""

    filename_lower = filename.lower()

    try:
        if filename_lower.endswith(".pdf"):
            # PDF Extraction
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += re.sub(r'\W+', ' ', extracted)

        elif filename_lower.endswith(".docx"):
            # Word Document Extraction
            text_content = docx2txt.process(uploaded_file)
            text += re.sub(r'\W+', ' ', text_content)

        elif filename_lower.endswith(".txt"):
            # Plain Text File Extraction
            text_content = uploaded_file.read().decode("utf-8", errors="ignore")
            text += re.sub(r'\W+', ' ', text_content)

        elif filename_lower.endswith((".xlsx", ".xls")):
            # Excel Extraction (all sheets, all cells)
            df_dict = pd.read_excel(uploaded_file, sheet_name=None)
            for sheet_name, df in df_dict.items():
                for col in df.columns:
                    for cell in df[col]:
                        if pd.notna(cell):
                            text += re.sub(r'\W+', ' ', str(cell)) + " "
        else:
            # Unsupported file type
            return ""

    except Exception as e:
        print(f"❌ Error extracting text from {filename}: {e}")

    print("✅ Text extracted:", text[:200], "...")  # Show only first 200 chars
    return text

def clean_table_lines(markdown_text):
    """Clean markdown table lines: remove empty lines, separators, and stray headers."""
    lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    cleaned = []
    for line in lines:
        # Skip markdown code fences
        if line.startswith("```"):
            continue
        # Skip separator rows like |---|---|
        if re.match(r"^\|\s*-+\s*\|", line):
            continue
        cleaned.append(line)
    return cleaned

def covert_response_to_testcases_single_sheet(markdown_text, test_collection,
                                              output_file=None):
    """
    Combine multiple markdown tables (possibly from multiple responses)
    into one clean Excel file without repeated headers or separator lines.
    """
    print("\n🚀 Starting markdown table to Excel conversion (clean version)...")

    # --- Normalize input ---
    if isinstance(markdown_text, list):
        markdown_text = "\n".join(str(line) for line in markdown_text)
    elif not isinstance(markdown_text, str):
        markdown_text = str(markdown_text)

    # --- Clean and split multiple tables ---
    markdown_text = markdown_text.replace("```", "")
    table_blocks = re.split(r"\n\s*\n", markdown_text)  # split at double newlines
    all_dfs = []
    master_header = None

    for block in table_blocks:
        table_lines = clean_table_lines(block)
        if len(table_lines) < 2 or "|" not in table_lines[0]:
            continue
        try:
            df = pd.read_csv(StringIO("\n".join(table_lines)), sep="|", engine="python", on_bad_lines="skip")
            df = df.dropna(axis=1, how="all")

            # Cleanup column names
            df.columns = [re.sub(r"\*+", "", col.strip()) for col in df.columns]

            # Remove empty/NaN rows
            df = df.dropna(how="all")

            # Strip extra spaces
            for col in df.select_dtypes(include="object").columns:
                df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

            # --- Handle repeated headers ---
            if master_header is None:
                master_header = list(df.columns)
            else:
                # Remove any rows where row values match header names
                df = df[~df.apply(lambda row: all(str(row[c]).strip().lower() == str(c).strip().lower()
                                                  for c in df.columns), axis=1)]

            all_dfs.append(df)
        except Exception as e:
            print(f"⚠️ Skipping invalid block due to parse error: {e}")

    if not all_dfs:
        print("⚠️ No valid markdown tables found to save.")
        return None

    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df = final_df.loc[:, ~final_df.columns.str.contains('^Unnamed')]

    # --- Prepare output file ---
    if not os.path.exists(test_collection):
        os.makedirs(test_collection)
        print(f"📁 Created output directory: {test_collection}")

    if not output_file:
        output_file = f"prompt_LLM_validator_{generate_random_prefix()}.xlsx"

    excel_path = os.path.join(test_collection, output_file)

    try:
        final_df.to_excel(excel_path, index=False, sheet_name="All_Prompts")
        print(f"✅ Cleaned markdown tables saved successfully: {excel_path}")
        return excel_path
    except PermissionError:
        print("❌ Permission denied. Please close the file if it’s open and retry.")
        return None