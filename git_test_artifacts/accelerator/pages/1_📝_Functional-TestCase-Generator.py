import streamlit as st
import os
import pandas as pd
from langchain_core.messages import HumanMessage
import PyPDF2
import re
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv


# Function to check file extension
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def main():
    st.set_page_config(
    page_title = "Functional Test Case Generator",  # 🔼 This sets the browser tab title
    page_icon = "📝",  # Optional: Add an emoji or favicon
    layout = "wide"
    )
    st.title("Functional Test Case Generator")
    st.write("Upload a PDF, Word, or Excel document:")

    #Uploading a PDF/DOC/EXCEL file code
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx', 'xlsx'])

    if uploaded_file is not None:
        if allowed_file(uploaded_file.name, ['pdf']):
            st.write("PDF file uploaded successfully!")
            # You can process PDF file here
        elif allowed_file(uploaded_file.name, ['docx']):
            st.write("Word file uploaded successfully!")
            # You can process Word file here
        elif allowed_file(uploaded_file.name, ['xlsx']):
            st.write("Excel file uploaded successfully!")
            # You can process Excel file here
        else:
            st.write("Unsupported file format. Please upload a PDF, Word, or Excel document.")

    if st.button("Extract doc and Generate"):
        if uploaded_file is not None:
            var = get_queries_from_ai_prompt(uploaded_file)
            st.write(var)

        else:
            st.error("Please upload a PDF file.")


    #A prompt text box
    Prompt = st.text_area('Enter the prompt Functional Test Case', '')

    if st.button("Generate Functional Test Cases"):
        prompt_response = get_queries_from_ai(Prompt)
        #st.markdown(prompt_response, unsafe_allow_html=True)  # Display HTML content
        st.write(prompt_response)

    st.divider()
    st.markdown("**👈 Select the required page from the sidebar** to continue!")


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

def extract_df(response):
    # Extracting the table data using regular expressions
    table_data = re.findall(r'\| (.+?) \| (.+?) \| (.+?) \|', response)

    # Creating DataFrame
    df = pd.DataFrame(table_data, columns=['Test Case ID','Test Case Description','Steps','Expected Result'])

    # Replacing empty strings with NaN for better representation
    df.replace('', pd.NA, inplace=True)

    return df

def get_queries_from_ai_prompt(uploaded_pdf):
    # Access the variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    # Set the environment variables explicitly if needed
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint
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
Tabular

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

def get_queries_from_ai(prompt):
    # Access the variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    # Set the environment variables explicitly if needed
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint

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
Tabular

Include examples where applicable.
Create the test cases in the similar format with the following requirement:
""" + prompt

    #Prompt for creating a Orthogonal array based questions
    model = AzureChatOpenAI(
        openai_api_version="2023-05-15",
        azure_deployment="qepracticekey",
    )
    message = HumanMessage(
        content=val2
    )
    output_value=model([message])
    return(output_value.content)



if __name__ == "__main__":
    main()
