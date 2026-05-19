import Prompt_generation as pro_gen
import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()
# --- Paths ---
current_path = os.getcwd()
prompt_collection = os.path.join(current_path, "prompt_collection")
os.makedirs(prompt_collection, exist_ok=True)

file_path = r"C:\Users\sathanantham.aru\Downloads\CPG_Domain_HighLevel_KnowledgeBase.pdf"
excel_path = r"C:\Users\sathanantham.aru\Downloads\Category.xlsx"

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Prompt Generation to Validate LLM", layout="wide")

# --- Title ---
st.title("🧠 Prompt Generation to Validate LLM")

st.markdown("""
This tool automatically generates **LLM validation prompts** based on uploaded requirement documents  
and optional Category–Subcategory mappings from Excel.
""")

# --- Upload Section ---
st.markdown("### 📄 Upload Requirement Document")
uploaded_req_file = st.file_uploader("Upload Requirement File (PDF, DOCX, TXT, etc.)", type=["pdf", "docx", "txt"])
if uploaded_req_file is not None:
    filename = uploaded_req_file.name.lower()

    if filename.endswith(".pdf"):
        st.success("PDF file uploaded successfully!")
        # Call your PDF extraction logic here
        # extracted_text = utils.extract_text_from_document(uploaded_file, filename)

    elif filename.endswith(".docx"):
        st.success("Word file uploaded successfully!")
        # Call your DOCX extraction logic here

    elif filename.endswith(".xlsx"):
        st.success("Excel file uploaded successfully!")
        # Call your Excel extraction logic here

    elif filename.endswith(".txt"):
        st.success("Text file uploaded successfully!")
        try:
            text_content = uploaded_req_file.read().decode("utf-8", errors="ignore")
        except Exception as e:
            st.error(f"Error reading TXT file: {e}")

    else:
        # This branch should rarely hit because file_uploader already restricts type
        st.error("Unsupported file format.")
st.markdown("### 📊 Upload Category–Subcategory Excel (Optional)")
uploaded_excel_file = st.file_uploader("Upload Excel File", type=["xlsx"])
# --- Generate Button ---
col1, col2 = st.columns(2)
with col1:
    generate_basic = st.button("🚀 Generate Prompt")
with col2:
    generate_conversation = st.button("🚀 Generate Conversational Prompt")
if generate_basic:
    if not uploaded_req_file:
        st.warning("⚠️ Please upload a requirement document before generating prompts.")
    else:
        with st.spinner("🔍 Extracting requirements and generating prompts... Please wait..."):
            # --- Step 1: Extract Requirements Directly from Uploaded File ---
            extracted_requirements=pro_gen.extract_text_from_document_streamlit(uploaded_req_file,uploaded_req_file.name)
            # --- Step 2: Read Excel Directly ---
            if uploaded_excel_file:
                cat_sub_pairs = pro_gen.read_category_subcategory_from_excel(uploaded_excel_file)
            else:
                cat_sub_pairs = []

            if not cat_sub_pairs:
                st.warning("⚠️ No Excel provided. Generating Category–Subcategory dynamically from requirements....")
                cat_sub_prompt=pro_gen.generate_category_prompt("category_subcatregory_geenration",requirements=extracted_requirements)
                cat_subcat_response=pro_gen.get_queries_from_ai_updated(cat_sub_prompt)
                print("************cat_sub_cat_detail*************")
                print(cat_subcat_response)
                cat_sub_pairs = pro_gen.parse_category_subcategory_from_response(cat_subcat_response)
                print("************cat_sub_cat_detail_final*************")
                print(cat_sub_pairs)
                #cat_sub_pairs = [("General", "All")]

            st.success(f"✅ Loaded {len(cat_sub_pairs)} category-subcategory pairs")

            # --- Step 3: Prepare Output Folder ---
            current_path = os.getcwd()
            prompt_collection = os.path.join(current_path, "prompt_collection")
            os.makedirs(prompt_collection, exist_ok=True)

            # --- Step 4: Generate Prompts ---
            all_prompts = []
            for category, subcategory in cat_sub_pairs:
                st.write(f"🧩 Generating prompts for → **{category}** / *{subcategory}*")

                constructed_prompt = pro_gen.generate_prompt(
                    "prompt_generation",
                    category,
                    subcategory,
                    extracted_requirements
                )

                response = pro_gen.generate_prompts_with_dynamic_stop(
                    constructed_prompt,
                    max_prompts=50,
                    min_new_threshold=5,
                    max_attempts=50
                )

                all_prompts.append(response)

            # --- Step 5: Save Output ---
            prompt_file=pro_gen.covert_response_to_testcases_single_sheet(all_prompts, prompt_collection)

            st.success("✅ All prompts generated and saved successfully!")
            st.info(f"📁 Saved to folder: `{prompt_collection}`")

            # --- Optional: Show download link if generated file is consistent ---
            generated_file = os.path.join(prompt_collection, prompt_file)
            if os.path.exists(generated_file):
                st.download_button(
                    label="⬇️ Download Generated Excel",
                    data=open(generated_file, "rb").read(),
                    file_name=prompt_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
elif generate_conversation:
    if not uploaded_req_file:
        st.warning("⚠️ Please upload a requirement document before generating prompts.")
    else:
        with st.spinner("🔍 Extracting requirements and generating prompts... Please wait..."):
            # --- Step 1: Extract Requirements Directly from Uploaded File ---
            extracted_requirements=pro_gen.extract_text_from_document_streamlit(uploaded_req_file,uploaded_req_file.name)
            # --- Step 2: Read Excel Directly ---
            if uploaded_excel_file:
                cat_sub_pairs = pro_gen.read_category_subcategory_from_excel(uploaded_excel_file)
            else:
                cat_sub_pairs = []

            if not cat_sub_pairs:
                st.warning("⚠️ No Excel provided. Generating Category–Subcategory dynamically from requirements....")
                cat_sub_prompt=pro_gen.generate_category_prompt("category_subcatregory_geenration",requirements=extracted_requirements)
                cat_subcat_response=pro_gen.get_queries_from_ai_updated(cat_sub_prompt)
                print("************cat_sub_cat_detail*************")
                print(cat_subcat_response)
                cat_sub_pairs = pro_gen.parse_category_subcategory_from_response(cat_subcat_response)
                print("************cat_sub_cat_detail_final*************")
                print(cat_sub_pairs)
                #cat_sub_pairs = [("General", "All")]

            st.success(f"✅ Loaded {len(cat_sub_pairs)} category-subcategory pairs")

            # --- Step 3: Prepare Output Folder ---
            current_path = os.getcwd()
            prompt_collection = os.path.join(current_path, "prompt_collection")
            os.makedirs(prompt_collection, exist_ok=True)

            # --- Step 4: Generate Prompts ---
            all_prompts = []
            for category, subcategory in cat_sub_pairs:
                st.write(f"🧩 Generating prompts for → **{category}** / *{subcategory}*")
                conversation_reminder = "Remember: each question must logically follow from the previous answer. Keep conversational continuity."
                constructed_prompt = pro_gen.generate_prompt(
                    "conversation_prompt",
                    category,
                    subcategory,
                    extracted_requirements
                )+ "\n\n" + conversation_reminder

                response = pro_gen.generate_prompts_with_dynamic_stop(
                    constructed_prompt,
                    max_prompts=30,
                    min_new_threshold=5,
                    max_attempts=50
                )

                all_prompts.append(response)

            # --- Step 5: Save Output ---
            prompt_file=pro_gen.covert_response_to_testcases_single_sheet(all_prompts, prompt_collection)

            st.success("✅ All prompts generated and saved successfully!")
            st.info(f"📁 Saved to folder: `{prompt_collection}`")

            # --- Optional: Show download link if generated file is consistent ---
            generated_file = os.path.join(prompt_collection, prompt_file)
            if os.path.exists(generated_file):
                st.download_button(
                    label="⬇️ Download Generated Excel",
                    data=open(generated_file, "rb").read(),
                    file_name=prompt_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
