import datetime
import os
from pathlib import Path
import base64
from setupconfig import *
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from openai import AzureOpenAI
import warnings; warnings.simplefilter(action='ignore')
from dotenv import load_dotenv; load_dotenv()
import PyPDF2
import docx2txt
from PIL import Image
import pytesseract
import re
import pandas as pd
from gherkin.token_scanner import TokenScanner
from gherkin.parser import Parser
import tldextract
from dotenv import load_dotenv
load_dotenv()
# Define the Langchain LLM model
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
# llm = AzureChatOpenAI(
#         openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
#         azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME"),
#         temperature=0,
#         max_tokens=None,
#         timeout=None,
#         max_retries=2,
#     )
llm=AzureChatOpenAI(
    openai_api_version="2023-05-15",
    azure_deployment="qepracticekey",
)

# Langchain LLM response
def get_response_from_llm(incoming: str) -> str:
    message = HumanMessage(
        content=incoming
    )
    output_value = llm([message])
    return (output_value.content)

# Initialize the Azure OpenAI LLM
openaillm = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# OpenAI LLM Chat response
def get_chat_completion_from_llm(incoming) -> str:
    try:
        response = openaillm.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=incoming
        )
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error in getting chat completion: {e}")
        return ""


def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded


def get_timestamped_filename(filename: str, app_url: str) -> str:
    path = Path(filename)
    fmt = "%d%b%Y_%I%M%p"
    extracted = tldextract.extract(app_url)
    timestamp = datetime.datetime.now().strftime(fmt)
    return f"{path.stem}_{extracted.domain}_{timestamp}{path.suffix}"

# Function to get a list of files from the specified path.
def get_files_from_path(path: str, only_extension=None) -> list:

    if not os.path.exists(path):
        return []
    new_files = []
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    if only_extension is not None:
        new_files = [f for f in files if (f.lower().endswith(f'.{only_extension}'))]
    else:
        new_files = files

    return new_files

# Function to extract text from PDF files
def extract_text_from_pdf(uploaded_pdf):
    text = ""
    pdf_filepath = os.path.join(step0_path, uploaded_pdf)
    pdf_reader = PyPDF2.PdfReader(pdf_filepath)
    num_pages = len(pdf_reader.pages)
    for page_number in range(num_pages):
        page = pdf_reader.pages[page_number]
        # Extract text and remove non-alphanumeric characters
        text += re.sub(r'\W+', ' ', page.extract_text())
    return text

# Function to extract text from images
def extract_text_from_image(uploaded_file):
    # Finding images and extracting text using pytesseract
    image_data = ""
    image_filepath = os.path.join(step0_path, uploaded_file)
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(image_filepath)

        # Extract text from the image using pytesseract
        try:
            extracted_text = pytesseract.image_to_string(image)
            if extracted_text:
                image_data += f"\nImage: {uploaded_file}\nExtracted Text: {extracted_text}\n"
            else:
                image_data += f"\nImage: {uploaded_file}\nExtracted Text: No text found\n"
        except Exception as e:
            print(f"Error extracting text from {uploaded_file}: {e}")
    return image_data

# Function to read the LLM response and save as dataframe
def extract_df(response):
    # Extracting the table data using regular expressions
    table_data = re.findall(r'\| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|', response)
    print(table_data)
    
    # Creating DataFrame
    df = pd.DataFrame(table_data, columns=['Test Case Name','Step Number','Test Step Description',
                                           'Test Step Expected Result','Status','Type'])

    # Replacing empty strings with NaN for better representation
    df.replace('', pd.NA, inplace=True)

    return df

# Function to save generated test cases to excel
def save_test_cases_excel(response, app_url):
    extracted_df = extract_df(response)
    output_filename = get_timestamped_filename(testcases_generated_file, app_url)
    output_path = os.path.join(step1_path, output_filename)
    # Write dataFrame to Excel file
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        extracted_df.to_excel(writer, sheet_name="testcases", index=False)
    
    return output_path

# Function to generate a feature file from the test cases
def generate_feature_file(excel_file_path, app_url):
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file_path)
        # Drop the last 2 columns
        df_new = df.iloc[:, :-2]
        extracted_text = df_new.to_csv(sep='|', index=False)

        # Create a feature file content using genAI test cases
        feature_content = ""
        with open(tc_to_feature_prompt, "r") as file:
                initial_prompt = file.read().strip()
        feature_prompt = initial_prompt.format(excel_data=extracted_text)

        feature_content = get_response_from_llm(feature_prompt)
        feature_content = feature_content.replace("```gherkin", "")
        feature_content = feature_content.replace("```", "")

        # Save the content to a .feature file
        feature_filename = get_timestamped_filename(testcase_feature_file, app_url)
        feature_filepath = os.path.join(step1_path, feature_filename)
        
        with open(feature_filepath, 'w') as file:
            file.write(feature_content)
        
        text = f"Feature file also generated at: {feature_filepath}"

    except Exception as e:
        print(e)
        text = f"Unable to generate Feature file."

    return text

# Function to check file extension
def check_allowed_file(filename):
    extension = '.' in filename and filename.rsplit('.', 1)[1].lower()
    check = extension in allowed_extensions
    return extension, check 

# Function to extract file extension
def get_file_extension(filename):
    extension = '.' in filename and filename.rsplit('.', 1)[1].lower()
    return extension

# Functiona identify type of files uploaded
def get_type_of_files(uploaded_files):

    if len(uploaded_files) == 1:
        uploaded_file = uploaded_files[0]
        file_type = get_file_extension(uploaded_file)
        if file_type in ['jpg', 'jpeg', 'png']:
            return 'images'
        else:
            return 'documents'
    else:
        list_of_types = []
        for uploaded_file in uploaded_files:
            file_type = get_file_extension(uploaded_file)
            list_of_types.append(file_type)
        
        if all(item in ['jpg', 'jpeg', 'png'] for item in list_of_types):
            return 'images'
        else:
            return 'documents'

# Functions to save uploaded file to desired path
def save_uploadedfile(uploadedfile, filepath):
    with open(os.path.join(filepath, uploadedfile.name), "wb") as f:
        f.write(uploadedfile.getbuffer())
    success_text = f"Saved File: {uploadedfile.name} to '{filepath}' in framework!"
    return success_text


def common_text_extractor(uploaded_files):
    
    extracted_text = ""
    if len(uploaded_files) == 1:
        uploaded_file = uploaded_files[0]
        file_type = get_file_extension(uploaded_file)

        if file_type == 'pdf':
            extracted_text = extract_text_from_pdf(uploaded_file)
        elif file_type == 'docx':
            docx_filepath = os.path.join(step0_path, uploaded_file)
            extracted_text = str(docx2txt.process(docx_filepath))
        elif file_type == 'xlsx':
            xlsx_filepath = os.path.join(step0_path, uploaded_file)
            xlsx_df = pd.read_excel(xlsx_filepath, engine='openpyxl')
            extracted_text = xlsx_df.to_csv(sep='\t', index=False)
        elif file_type in ['jpg', 'jpeg', 'png']:
            extracted_text = extract_text_from_image(uploaded_file)
    else:
        for uploaded_file in uploaded_files:
            file_type = get_file_extension(uploaded_file)

            if file_type == 'pdf':
                extracted_text += extract_text_from_pdf(uploaded_file) + "\n"
            elif file_type == 'docx':
                docx_filepath = os.path.join(step0_path, uploaded_file)
                extracted_text += str(docx2txt.process(docx_filepath)) + "\n"
            elif file_type == 'xlsx':
                xlsx_filepath = os.path.join(step0_path, uploaded_file)
                xlsx_df = pd.read_excel(xlsx_filepath, engine='openpyxl')
                extracted_text += xlsx_df.to_csv(sep='\t', index=False) + "\n"
            elif file_type in ['jpg', 'jpeg', 'png']:
                extracted_text += extract_text_from_image(uploaded_file) + "\n"
    
    return extracted_text

# Function to generate test cases using the LLM
def generate_test_cases(uploaded_files, app_url, extra_prompt=None):

    removed_text = common_text_extractor(uploaded_files)
    summarized_text = summarize_prompt_contents(removed_text)
    # print("Final extracted text:", removed_text)
    type_of_files = get_type_of_files(uploaded_files)

    if type_of_files == 'images':
        with open(tc_from_image_prompt, "r") as file:
            initial_prompt = file.read().strip()
        final_prompt = initial_prompt.format(app_data=app_url, image_data=summarized_text)
    else:
        with open(testcases_prompt, "r") as file:
            initial_prompt = file.read().strip()
        final_prompt = initial_prompt.format(app_data=app_url, prompt_data=summarized_text)

    if extra_prompt is not None:
        final_prompt += "\nAdditional Instructions: " + extra_prompt
    
    response = get_response_from_llm(final_prompt)

    return response

# Declaring global variables for feature file parsing
scenario_prompts = []
feat_prompt = None

# Function to parse feature and prompt
def parse_feature_file(feature_file_path: str):
    try:
        with open(feature_file_path, "r") as file:
            gherkin_content = file.read().strip()

        # Parse Gherkin feature file
        parser = Parser()
        document = parser.parse(TokenScanner(gherkin_content))
        feature = document['feature']
        scenario_strings = []
        background_steps = []
        
        for item in feature["children"]:
            if "background" in item:
                background_steps = [step["text"] for step in item["background"]["steps"]]
                break  # Only one background is expected
        
        if background_steps != []:
            background_text = " \n ".join(background_steps)

        for item in feature["children"]:
            if "scenario" in item:
                scenario = item["scenario"]
                scenario_name = scenario["name"]
                steps = scenario["steps"]
                steps_text = " \n ".join(step["text"] for step in steps)
                scenario_entry = f"{scenario_name}: {steps_text}"
                # Combine all step texts into a single string
                if background_steps != []:
                    all_steps = "Background: " + background_text + ". Scenario: " + scenario_entry
                else:
                    all_steps = "Scenario: " + scenario_entry
                scenario_strings.append(all_steps)

        with open(each_scenario_prompt, "r") as f:
            prefix = f.read().strip()

        global scenario_prompts
        scenario_prompts = [prefix + item for item in scenario_strings]

        with open(execution_prompt, "r") as file:
            initial_prompt = file.read().strip()

        global feat_prompt
        feat_prompt = initial_prompt.format(gherkin_data=gherkin_content)

    except Exception as e:
        print(f"Error Parsing file: {e}")

# Function to generate report prompt
def generate_report_prompt():
    with open(report_gen_prompt, "r") as file:
        report_prompt = file.read().strip()

    return report_prompt

# Function to display HTML report in streamlit page
def display_html_report(response: str):
    html = ""
    pattern = r'(.*?)``````(.*)'
    result = re.sub(pattern, r'\2', response, flags=re.DOTALL)
    result = result.replace("```html", "")
    result = result.replace("```", "")
    html = result
    return html

def save_html_report(content, link):
    html_filename = get_timestamped_filename(execution_report_file, link)
    report_filepath = step3_path + html_filename
    with open(report_filepath, "w+") as f:
        f.write(content)
    return (f"Saved report to location: {report_filepath}")

# Function to summarize the chat contents to reduce tokens
def summarize_prompt_contents(incoming: str) -> str:
    with open(summary_prompt, "r") as f:
        summarize = f.read().format(content_data=incoming)
    outgoing = get_response_from_llm(summarize)
    return outgoing

# Function to recursively update the permissions
def chmod_recursive(path, mode):
    for root, dirs, files in os.walk(path):
        os.chmod(root, mode)
        for d in dirs:
            os.chmod(os.path.join(root, d), mode)
        for f in files:
            os.chmod(os.path.join(root, f), mode)

            