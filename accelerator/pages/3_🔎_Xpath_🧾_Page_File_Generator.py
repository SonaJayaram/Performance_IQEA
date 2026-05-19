from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import streamlit as st
import uuid
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import Utilities_Xpath as utils
# Initialize session state for the popup
if "show_popup" not in st.session_state:
    st.session_state.show_popup = False
if "show_form" not in st.session_state:
    st.session_state.show_form = False
# Initialize session state for selected XPaths and prompt response
if 'selected_xpaths' not in st.session_state:
    st.session_state.selected_xpaths = []
if 'prompt_response' not in st.session_state:
    st.session_state.prompt_response = ""
if 'prompt_response_page_file' not in st.session_state:
    st.session_state.prompt_response_page_file=""
if 'driver' not in st.session_state:
    st.session_state.driver = None
if 'last_page' not in st.session_state:
    st.session_state.last_page = None
if 'selected_tags' not in st.session_state:
        st.session_state.selected_tags = []
if 'selected_app' not in st.session_state:
    st.session_state.selected_app = []
# Unique key for session state
if "scroll_to_top" not in st.session_state:
    st.session_state.scroll_to_top = False

st.title("XPath Generator for Visible Elements")
page_url = st.text_input("Enter the URL of the page:")
selected_app = st.multiselect(
        "Select application type:",
        ["PowerBi", "Web"],
        default=["Web"])
tags_placeholder = st.empty()
if "Web" in selected_app:
    selected_tags = tags_placeholder.multiselect(
        "Select element types to extract:",
        ["input", "button", "a", "select", "textarea", "div", "span", "All"],
        default=["input", "button"]
    )
else:
    tags_placeholder.empty()  # Hides the tag selection for PowerBi only
    selected_tags = []  # No tags for PowerBi
if st.button("Open Browser"):
    if page_url:
        st.session_state.selected_tags = selected_tags
        st.session_state.selected_app = selected_app
        chrome_options = Options()
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        #service = Service(ChromeDriverManager().install())
        # service = Service(r"C:\Users\sathanantham.aru\PycharmProjects\ai-accelerator\Input\chromedriver.exe")
        # st.session_state.driver = webdriver.Chrome(service=service, options=chrome_options)
        st.session_state.driver = webdriver.Chrome(options=chrome_options)
        st.session_state.driver.get(page_url)
        st.session_state.driver.maximize_window()
        WebDriverWait(st.session_state.driver, 30).until(utils.is_page_loaded)

        st.info("Browser opened.")
st.markdown("<a name='top-button'></a>", unsafe_allow_html=True)
collect_clicked = st.button("Collecting Elements", key="collect_btn")
if collect_clicked:
    formatted_summary = None
    st.session_state.selected_xpaths = []
    st.session_state.prompt_response = ""
    page_identifier = st.session_state.driver.current_url# Collect visible elements
    if "PowerBi" in selected_app:
        formatted_summary = utils.get_visible_element_powerBi(st.session_state.driver,page_identifier)
            #get_visible_element_iframe(st.session_state.driver,page_identifier,st.session_state.selected_tags))
    if"Web" in selected_app:
        formatted_summary = utils.get_visible_element_iframe(st.session_state.driver, page_identifier,
                                                       st.session_state.selected_tags)
    if formatted_summary is None:
        formatted_summary = []
    if formatted_summary:
        if "PowerBi" in selected_app:
        #prompt = f"Generate multiple XPath expressions for the input and button elements based on the following details. Consider various attributes, hierarchy levels, and text content to create comprehensive XPath variations for each element: {formatted_summary}"
            st.session_state.prompt_response = utils.get_queries_from_ai("PowerBi",formatted_summary)
            print("OPen Ai response" + st.session_state.prompt_response)
        if "Web" in selected_app:
        #prompt = f"Generate multiple XPath expressions for the input and button elements based on the following details. Consider various attributes, hierarchy levels, and text content to create comprehensive XPath variations for each element: {formatted_summary}"
            st.session_state.prompt_response = utils.get_queries_from_ai("Web",formatted_summary)
            print("OPen Ai response" + st.session_state.prompt_response)
    else:
        st.info("No elements found in selected tag")
    # Simulate the AI response for demonstration

# Display the XPath selection UI only after receiving a prompt response
if st.session_state.prompt_response:
    xpath_dict = utils.filter_duplicate_xpaths(utils.selecting_xpath(st.session_state.prompt_response))
    print(xpath_dict)
    st.title("Select XPath Expressions to Add to Excel")

    st.session_state.selected_xpaths=utils.adding_xapth_user_view(xpath_dict)
    page_name = st.text_input("Enter the Page Name:")
    # Show "Add Selected XPaths to Excel" button only after XPaths are displayed
    if st.button("Add Selected XPaths to Excel"):
        print("going inside add excel")
        print(st.session_state.selected_xpaths)
        if st.session_state.selected_xpaths:
            print("going inside add excel")
            utils.adding_selected_xapth_excel(page_name)
            st.session_state.show_popup = True
            st.session_state.show_form = False  # Reset form visibility
        # Show popup only if the flag is set
if st.session_state.show_popup and not st.session_state.show_form:
    st.write("**Do you want to generate the page file?**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            st.session_state.show_popup = False  # Hide popup
            st.session_state.show_form = True  # Show form for page file generation

    with col2:
        if st.button("No"):
            st.session_state.show_popup = False
            st.session_state.show_form = False
            st.write("Page file generation skipped.")
# Show popup only if the flag is set
if st.session_state.show_form:
    st.write("Generating Page File")
    page_name = st.text_input("Enter Page Name", value=page_name)
    language = st.selectbox("Select Language", ["java", "python", "c#", "javascript"])


    if st.button("Generate Page File"):
        st.session_state.prompt_response_page_file = ""
        Prompt = utils.generate_pom_from_excel("Page_File",page_name,language)
        st.session_state.prompt_response_page_file = utils.get_queries_from_ai("Page_File",Prompt)
        st.subheader("Generated Page Class")
        utils.create_java_file(page_name,language,st.session_state.prompt_response_page_file)
        # with open("GeneratedTest.java", "w") as file:
        #     file.write(st.session_state.prompt_response)
        # print("✅ Java test script generated: GeneratedTest.java")
        #st.code(st.session_state.prompt_response)
        # Placeholder for your page file generation script
        st.success(f"Page file generated for '{page_name}' in '{language}' language.")
        # Trigger scroll with 'Continue' button
        # if st.button("Continue"):
        #     utils.scroll_and_focus()


#Handle the "Find XPath" button logic
if st.session_state.driver:
  if st.button("Find XPath for new page"):
    formatted_summary = None
    st.session_state.selected_xpaths = []
    st.session_state.prompt_response = ""
    st.session_state.prompt_response_page_file = ""
    st.session_state.show_popup = False
    st.session_state.show_form = False
    utils.loading_newpage(st.session_state.driver)
    page_identifier = st.session_state.driver.current_url

    if "PowerBi" in selected_app:
        formatted_summary = utils.get_visible_element_powerBi(st.session_state.driver, page_identifier)
    if "Web" in selected_app:
        formatted_summary = utils.get_visible_element_iframe(st.session_state.driver, page_identifier, selected_tags)
    # Ensure current_elements is always defined (even if empty)
    if formatted_summary is None:
        formatted_summary = []
    if formatted_summary:
        if "PowerBi" in selected_app:
        #prompt = f"Generate multiple XPath expressions for the input and button elements based on the following details. Consider various attributes, hierarchy levels, and text content to create comprehensive XPath variations for each element: {formatted_summary}"
            st.session_state.prompt_response = utils.get_queries_from_ai("PowerBi",formatted_summary)
            print("OPen Ai response" + st.session_state.prompt_response)
        if "Web" in selected_app:
        #prompt = f"Generate multiple XPath expressions for the input and button elements based on the following details. Consider various attributes, hierarchy levels, and text content to create comprehensive XPath variations for each element: {formatted_summary}"
            st.session_state.prompt_response = utils.get_queries_from_ai("Web",formatted_summary)
            print("OPen Ai response" + st.session_state.prompt_response)
        # prompt = f"Generate multiple XPath expressions for the input and button elements based on the following details. Consider various attributes, hierarchy levels, and text content to create comprehensive XPath variations for each element: {current_elements}"
        # st.session_state.prompt_response = get_queries_from_ai(prompt)
        # print("open Ai Reponse" + st.session_state.prompt_response)
    else:
        st.info("No elements found in selected tag")


    # Display the XPath selection UI only after receiving a prompt response
    if st.session_state.prompt_response:
        xpath_dict = utils.filter_duplicate_xpaths(utils.selecting_xpath(st.session_state.prompt_response))
        print(xpath_dict)

        st.title("Select XPath Expressions from new page to Add to Excel")
        try:
            utils.adding_xapth_user_view(xpath_dict)
        except (Exception) as e:
            print(e)
        new_page_name = st.text_input("Enter the New Page Name:", key="new_page_name")
        #new_page_name = st.text_input("Enter the New Page Name:")
        # Show "Add Selected XPaths to Excel" button only after XPaths are displayed
        Add_to_excel = st.button("Add Selected XPaths to Excel", key="add_to_excel_new")
        if Add_to_excel:
            if st.session_state.selected_xpaths:
                utils.adding_selected_xapth_excel(new_page_name)
                st.session_state.show_popup = True
                st.session_state.show_form = False  # Reset form visibility
            # Show popup only if the flag is set
            if st.session_state.show_popup and not st.session_state.show_form:
                st.write("**Do you want to generate the page file?**")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes"):
                        st.session_state.show_popup = False  # Hide popup
                        st.session_state.show_form = True  # Show form for page file generation

                with col2:
                    if st.button("No"):
                        st.session_state.show_popup = False
                        st.session_state.show_form = False
                        st.write("Page file generation skipped.")
            # Show popup only if the flag is set
            if st.session_state.show_form:
                st.write("Generating Page File")
                page_name = st.text_input("Enter Page Name", value=page_name)
                language = st.selectbox("Select Language", ["java", "python", "c#", "javascript"])

                if st.button("Generate Page File"):
                    st.session_state.prompt_response_page_file = ""
                    Prompt = utils.generate_pom_from_excel("Page_File", page_name, language)
                    st.session_state.prompt_response_page_file = utils.get_queries_from_ai("Page_File", Prompt)
                    st.subheader("Generated Page Class")
                    utils.create_java_file(page_name, language, st.session_state.prompt_response_page_file)
                    st.session_state.show_popup = False
                    st.session_state.show_form = False
                    st.success(f"Page file generated for '{page_name}' in '{language}' language.")
                    # # Trigger scroll with 'Continue' button
                    # if st.button("Continue"):
                    #     utils.scroll_and_focus()
