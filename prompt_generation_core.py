import Prompt_generation as pro_gen
import os
from dotenv import load_dotenv
load_dotenv()
# --- Paths ---
current_path = os.getcwd()
prompt_collection = os.path.join(current_path, "prompt_collection")
os.makedirs(prompt_collection, exist_ok=True)

file_path = r"C:\Users\sathanantham.aru\Downloads\CPG_Domain_HighLevel_KnowledgeBase.pdf"
excel_path =None
#excel_path = r"C:\Users\sathanantham.aru\Downloads\Category.xlsx"

# --- Step 1: Extract requirements text ---
extracted_requirements = pro_gen.extract_text_from_document(file_path)

# --- Step 2: Read Category–Subcategory pairs from Excel ---
if excel_path:
    cat_sub_pairs = pro_gen.read_category_subcategory_from_excel(excel_path)
else:
    cat_sub_pairs=None
if not cat_sub_pairs:
    cat_sub_prompt = pro_gen.generate_category_prompt("category_subcatregory_geenration",
                                                      requirements=extracted_requirements)
    cat_subcat_response = pro_gen.get_queries_from_ai_updated(cat_sub_prompt)
    print("************cat_sub_cat_detail*************")
    print(cat_subcat_response)
    cat_sub_pairs = pro_gen.parse_category_subcategory_from_response(cat_subcat_response)
    print("************cat_sub_cat_detail_final*************")
    print(cat_sub_pairs)
else:
    print(f"✅ Loaded {len(cat_sub_pairs)} category-subcategory pairs.")

# --- Step 3: Iterate and Generate Prompts ---
prompt_response = []

for category, subcategory in cat_sub_pairs:
    print(f"\n🧩 Generating test cases for → Category: {category}, Subcategory: {subcategory}")

    constructed_prompt = pro_gen.generate_prompt(
        "prompt_generation",
        category,
        subcategory,
        extracted_requirements
    )

    response = pro_gen.generate_prompts_with_dynamic_stop(
        constructed_prompt,
        10,
        5,
        max_attempts=50
    )

    prompt_response.append(response)
print(prompt_response)
# --- Step 4: Save AI output to Excel ---
pro_gen.covert_response_to_testcases_single_sheet(prompt_response, prompt_collection)
print(prompt_response)
print("✅ All test cases generated and saved successfully!")
