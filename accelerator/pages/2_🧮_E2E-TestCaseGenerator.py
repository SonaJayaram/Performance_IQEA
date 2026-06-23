import streamlit as st
from langchain_core.messages import HumanMessage
from PIL import Image
import pytesseract
from langchain_openai import AzureChatOpenAI
import streamlit.components.v1 as components
from dotenv import load_dotenv
import os

load_dotenv()
from Utilities import *


# Function to check file extension
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def main():
    st.set_page_config(
        page_title="Test Case Generator",  # 🔼 This sets the browser tab title
        page_icon="🧮",  # Optional: Add an emoji or favicon
        layout="wide"  # Optional: 'centered' or 'wide'
    )

    #Title of the Page
    st.title("Test Case Generator")

    st.write("Select the image flows related to a user story")
    # Image folder path
    IMAGE_FOLDER = "./data/images"  # Change this to your image folder

    if "selected_images" not in st.session_state:
        st.session_state.selected_images = []

    # Get image filenames
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    # --- Display heading and image buttons ---
    st.write("### Hover to preview")
    html_content = generate_hoverable_image_buttons(IMAGE_FOLDER, image_files)
    components.html(html_content, height=350, scrolling=True)


    # --- Capture query param (simulate button click) ---
    query_params = st.query_params
    selected = query_params.get("selected")
    if selected and selected not in st.session_state.selected_images:
        st.session_state.selected_images.append(selected)

    # Track selected order
    if "selected_images" not in st.session_state:
        st.session_state.selected_images = []

    st.write("### Click image names in the order you want to select them:")

    # Show buttons for each image
    for img in image_files:
        if img not in st.session_state.selected_images:
            if st.button(img):
                st.session_state.selected_images.append(img)

    # Show selected image names in order
    if st.session_state.selected_images:
        st.write("### Selected in order:")
        for i, name in enumerate(st.session_state.selected_images, 1):
            st.write(f"{i}. {name}")

    # Option to reset selection
    if st.button("Reset Selection"):
        st.session_state.selected_images = []

    #A prompt text box
    prompt = st.text_area('Enter the prompt Functional Test Case', '')

    if st.session_state.selected_images and prompt:
        # Construct navigation as a comma-separated string
        navigation = ', '.join(st.session_state.selected_images)

        # Finding images in the pages folder and extracting text using pytesseract
        image_data = ""
        for image_name in st.session_state.selected_images:
            image_path = os.path.join(IMAGE_FOLDER, image_name)
            if os.path.exists(image_path):
                # Display the uploaded image
                image = Image.open(image_path)
                st.image(image, caption=image_name, use_container_width=True)

                # Extract text from the image using pytesseract
                try:
                    extracted_text = pytesseract.image_to_string(image)
                    if extracted_text:
                        image_data += f"\nImage: {image_name}\nExtracted Text: {extracted_text}\n"
                    else:
                        image_data += f"\nImage: {image_name}\nExtracted Text: No text found\n"
                except Exception as e:
                    st.error(f"Error extracting text from {image_name}: {e}")
            else:
                st.error(f"Image not found: {image_name}")

    if st.button("Generate Functional Test Cases"):
        prompt_response = get_queries_from_ai(prompt, navigation, image_data)
        st.write(prompt_response)


def get_queries_from_ai(prompt, navigation, image_data):
    # Access the variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    # Set the environment variables explicitly if needed
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint


    constructedprompt =f"""
Consider the navigation of the Page as provided below in the same order of selection:
Navigation Flow: {navigation}
Image Context:
{image_data}

Use the navigation flow provided to understand the sequence of pages, but do not create test cases for each page or image. 
The navigation should only be used to set the context for the test case flow until reaching the page related to the requirement. 
Once the required page is reached, create test cases specifically for the given requirement, ignoring intermediate pages or images.

Act as a Functional Test Case Generator. Based on the given Requirement, create detailed and comprehensive test cases using the Orthogonal Array technique. 
Each test case should have multiple steps, covering a sequence of actions to verify functionality. 
Use the following columns in the output Excel sheet:
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
- Write all the possible Test cases and only include the PNG file name without the .png extension.

Important:
- The test cases should be created only for the given requirement. 
- Navigation flow should only be used to understand the context of reaching the requirement page.
- Do not generate test cases for intermediate pages or navigation steps. 

Ensure that each test case output:
- The Test Cases created should be only in a Excel sheet format with the format explained above

Include examples where applicable.
Create 10 independent End to end test cases in the similar format for the following requirement using the navigation only to create the flow prior to the start with requirement flow:
{prompt}
"""

    #Prompt for creating a Orthogonal array based questions
    try:
        model = AzureChatOpenAI(
            openai_api_version="2023-05-15",
            azure_deployment="qepracticekey",
        )
        message = HumanMessage(content=constructedprompt)
        output_value=model([message])
        st.success("Generated Test Cases:")
        return(output_value.content)
    except Exception as e:
        st.error(f"Error during OpenAI call: {e}")


if __name__ == "__main__":
    main()
